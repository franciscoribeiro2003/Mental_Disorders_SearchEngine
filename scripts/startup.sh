#!/bin/bash

# Define core names and schema paths inside the container
CORE1="disorders"
CORE2="disorders02"
CORE3="disorders03"
SCHEMA1="solr/simple_schema.json"
SCHEMA2="solr/schema02.json"
SCHEMA3="solr/schema03.json"
DATA_FILE="/data/data/final.json"
DATA_FILE2="/data/data/final_embedded.json"
CONTAINER_NAME="meic_solr"

# Stop and remove any existing Solr container with the specified name
docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME

# Start the Solr container with a volume mapping to the project root
# This maps the project root to /data in the container, making all files accessible
docker run -p 8983:8983 --name $CONTAINER_NAME -v "$(pwd):/data" -d solr:9

# Wait for Solr to fully initialize
echo "Waiting for Solr to start..."
sleep 4  # Adjust if Solr requires more time to start

# Copy the synonyms file into the container
echo "Copying synonyms file into Solr container..."
docker cp solr/synonyms_disorders.txt $CONTAINER_NAME:/opt/solr/server/solr/configsets/_default/conf/

# Create CORE1 and apply schema from the mapped file path
docker exec -it $CONTAINER_NAME solr create_core -c $CORE1
curl -X POST -H 'Content-type:application/json' \
    --data-binary "@$SCHEMA1" \
    http://localhost:8983/solr/$CORE1/schema

# Create CORE2 and apply schema from the mapped file path
docker exec -it $CONTAINER_NAME solr create_core -c $CORE2
curl -X POST -H 'Content-type:application/json' \
    --data-binary "@$SCHEMA2" \
    http://localhost:8983/solr/$CORE2/schema

# Apply schema03 to CORE3
docker exec -it $CONTAINER_NAME solr create_core -c $CORE3
curl -X POST -H 'Content-type:application/json' \
    --data-binary "@$SCHEMA3" \
    http://localhost:8983/solr/$CORE3/schema

# Populate both cores with data, if the data file exists
if [ -f "$(pwd)/data/final.json" ]; then
    docker exec -it $CONTAINER_NAME solr post -c $CORE1 $DATA_FILE
    docker exec -it $CONTAINER_NAME solr post -c $CORE2 $DATA_FILE
    docker exec -it $CONTAINER_NAME solr post -c $CORE3 $DATA_FILE2
else
    echo "Data file 'final.json' not found in 'data' directory. Skipping data import."
fi

echo "Solr container with cores '$CORE1' and '$CORE2' started and populated successfully."
