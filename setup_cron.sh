#!/bin/bash

# This script sets up a cron job to run the data fetcher daily

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a temporary crontab file
TEMP_CRON=$(mktemp)

# Export existing crontab to the temporary file
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "" > "$TEMP_CRON"

# Check if the job already exists
if ! grep -q "fetch_fed_register.py" "$TEMP_CRON"; then
    # Add the new job to run daily at 2:00 AM
    echo "# Federal Documents Data Fetcher - runs daily at 2:00 AM" >> "$TEMP_CRON"
    echo "0 2 * * * cd $DIR && python3 improved_data_fetcher.py >> $DIR/data_fetcher.log 2>&1" >> "$TEMP_CRON"
    
    # Install the updated crontab
    crontab "$TEMP_CRON"
    echo "Cron job installed successfully! The data fetcher will run daily at 2:00 AM."
else
    echo "Cron job already exists."
fi

# Clean up
rm "$TEMP_CRON"

# Run the data fetcher once immediately
echo "Fetching data for the first time..."
cd "$DIR" && python3 improved_data_fetcher.py

echo "Setup complete!"
