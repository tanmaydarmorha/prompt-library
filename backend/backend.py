import os
from datetime import datetime
from random import choices, randint
from typing import List

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from models.Prompt import Prompt
from models.create_request_args import CreateRequestArgs
from models.update_request_args import UpdateRequestArgs

app = FastAPI()

# MongoDB connection configuration
MONGO_HOST = os.getenv('MONGO_HOST', 'mongodb')
MONGO_PORT = int(os.getenv('MONGO_PORT', '27017'))
MONGO_DB = os.getenv('MONGO_DB', 'your_database_name')
MONGO_USER = os.getenv('MONGO_USER', 'admin')
MONGO_PASS = os.getenv('MONGO_PASS', 'password')

client = MongoClient(
    host=MONGO_HOST,
    port=MONGO_PORT,
    username=MONGO_USER,
    password=MONGO_PASS,
    authSource='admin'
)
db = client[MONGO_DB]
collection = db['prompts']


@app.get("/prompts", response_model=List[Prompt])
def get_prompts():
    try:
        # Retrieve the documents from MongoDB
        prompts = list(collection.find())

        # Create a local variable to store the converted Prompt instances
        prompt_list = []

        # Iterate over each prompt document and create Prompt instances
        for prompt in prompts:
            print(prompt["_id"])
            prompt_instance = Prompt(
                id=str(prompt["_id"]),  # Convert ObjectId to string
                prompt=prompt["prompt"],
                promptTitle=prompt["promptTitle"],
                promptDescription=prompt["promptDescription"],
                createdBy=prompt["createdBy"],
                createdDateTime=prompt["createdDateTime"],
                lastUpdatedBy=prompt["lastUpdatedBy"],
                lastUpdatedDateTime=prompt["lastUpdatedDateTime"]
            )
            print(prompt_instance)
            # Append the created Prompt instance to the list
            prompt_list.append(prompt_instance)

        # Return the local variable
        return prompt_list
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/prompt", response_model=Prompt, status_code=201)
def create_prompt(request: CreateRequestArgs):
    """
    Create a new prompt in the MongoDB database with auto-generated dates and lastUpdatedBy.
    """
    # Set the current time for createdDateTime and lastUpdatedDateTime
    current_time = datetime.now()

    # Create the prompt data using the request data
    prompt_data = {
        "prompt": request.prompt,
        "promptTitle": request.promptTitle,
        "promptDescription": request.promptDescription,
        "createdBy": request.createdBy,
        "createdDateTime": current_time,
        "lastUpdatedBy": request.createdBy,  # Set lastUpdatedBy as createdBy
        "lastUpdatedDateTime": current_time
    }

    # Insert the prompt data into MongoDB and retrieve the inserted ID
    result = collection.insert_one(prompt_data)
    prompt_data["id"] = str(result.inserted_id)  # Change _id to id

    # Return the created prompt with ID
    return Prompt(**prompt_data)


@app.put("/prompt/{prompt_id}", response_model=Prompt)
def update_prompt(prompt_id: str, request: UpdateRequestArgs):
    # Prepare an update dictionary to hold non-null fields
    update_dict = {}

    if request.updatedBy is None:
        raise HTTPException(status_code=403, detail="User missing from request")

    # Check each field in the request and add it to the update_dict if it's not None
    if request.prompt is not None:
        update_dict['prompt'] = request.prompt
    if request.promptTitle is not None:
        update_dict['promptTitle'] = request.promptTitle
    if request.promptDescription is not None:
        update_dict['promptDescription'] = request.promptDescription

    # Always update lastUpdatedDateTime to the current time
    update_dict['lastUpdatedDateTime'] = datetime.now()

    # Perform the update in the database
    result = collection.find_one_and_update(
        {'_id': ObjectId(prompt_id)},
        {'$set': update_dict},
        return_document=True
    )

    if result is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Include ID in the updated prompt response
    result["id"] = str(result["_id"])  # Change _id to id
    result.pop("_id")  # Remove the original _id field

    return Prompt(**result)


@app.delete("/prompt/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: str):
    result = collection.delete_one({'_id': ObjectId(prompt_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prompt not found")


@app.post("/create-seed-data")
def create_seed_data(num_records: int = Query(10, ge=1, le=100)):
    """
    Creates seed data for prompts in the database.

    Parameters:
    - num_records (int): The number of prompt records to create (default is 10, must be between 1 and 100).
    """
    try:
        prompts = []
        for _ in range(num_records):
            prompt = Prompt(
                id=str(ObjectId()),  # Use 'id' instead of '_id'
                prompt=f"Prompt {randint(1, 100)}",
                promptTitle=f"Sample Prompt {randint(1, 100)}",
                promptDescription=f"This is a sample prompt description {randint(1, 100)}",
                createdBy=choices(["John Doe", "Jane Smith", "Emily Johnson", "Michael Davis"], k=1)[0],
                createdDateTime=datetime.now(),
                lastUpdatedBy=choices(["John Doe", "Jane Smith", "Emily Johnson", "Michael Davis"], k=1)[0],
                lastUpdatedDateTime=datetime.now()
            )
            prompts.append(prompt)

        result = collection.insert_many([p.dict(by_alias=True) for p in prompts])
        return {"message": f"{len(result.inserted_ids)} prompts created successfully"}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while creating seed data")
