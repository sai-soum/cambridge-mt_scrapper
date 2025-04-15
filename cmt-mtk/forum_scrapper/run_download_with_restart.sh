#!/bin/bash

# List of JSON paths (modify accordingly)
JSON_FILES=(
    # "/data4/soumya/MSF_forum/metadata/Discussion Zone - Pop, Singer-Songwriter.json"
    "/data4/soumya/MSF_forum/metadata/Discussion Zone - Rock, Punk, Metal.json"
    # "/data4/soumya/MSF_forum/metadata/Discussion Zone - Electronica, Dance, Experimental, Spoken Word.json"
    # "/data4/soumya/MSF_forum/metadata/Discussion Zone - Hip-hop, R&B, Soul.json"
    # "/data4/soumya/MSF_forum/metadata/Discussion Zone - Acoustic, Jazz, Country, Orchestral.json"
    # "/data4/soumya/MSF_forum/metadata/Discussion Zone - Alt Rock, Blues, Country Rock, Indie, Funk, Reggae.json"
    
)

# Set the audio save directory
AUDIO_DIR="/data4/soumya/MSF_forum/dataset"

# Loop through JSON files
for JSON_PATH in "${JSON_FILES[@]}"; do
    echo "Processing: $JSON_PATH"
    
    while true; do
        python3 /home/soumya/cambridge-mt_scrapper/cmt-mtk/forum_scrapper/download_forum_mixes_with_shutdown.py "$JSON_PATH" "$AUDIO_DIR"
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo "Completed $JSON_PATH successfully."
            break
        elif [ $EXIT_CODE -eq 1 ]; then
            echo "Encountered multiple 400 errors. Restarting in 30 seconds..."
            sleep 30
        else
            echo "Unknown error occurred."
            break
        fi
    done
done

echo "All downloads completed!"