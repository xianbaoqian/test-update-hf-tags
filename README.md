# Update LLM Tags Script

This script is designed to identify and update repositories on Hugging Face that are likely using the Transformers library but are not properly tagged. It performs a series of checks and filters to identify potential repositories, allows for manual confirmation, and can create pull requests to update the metadata.

## Features

- Fetches repositories without library tags
- Identifies repositories likely using Transformers
- Filters out repositories with existing PRs
- Allows manual confirmation of repositories
- Creates pull requests to update metadata

## Prerequisites

- Python 3.7+
- Required Python packages (install via `pip install -r requirements.txt`):
  - huggingface_hub
  - pyyaml
  - python-dotenv

## Setup

1. Clone this repository
2. Install the required packages: `pip install -r requirements.txt`
3. Create a `.env` file in the root directory with your Hugging Face token:
   ```
   HF_TOKEN=your_huggingface_token_here
   ```

## Usage

1. Run the dry run:
   ```
   python update-llm-tags.py
   ```
   This will perform all checks and filters without making any changes.

2. Review the generated files:
   - `all_repos.yaml`: List of all fetched repositories
   - `filtered_repos.yaml`: Repositories categorized by different filters
   - `processed_repos.yaml`: Final list of repositories to be updated

3. If you're satisfied with the dry run results, run the script again and confirm when prompted to proceed with the updates.

## How it works

1. Fetches repositories without library tags
2. Identifies repositories likely using Transformers based on file structure and content
3. Filters out repositories with existing PRs
4. Checks for explicit Transformers imports in README files
5. Allows manual confirmation for ambiguous cases
6. Creates pull requests to update metadata for confirmed repositories

## Notes

- The script uses a cache (`model_info_cache.pkl`) to store repository information and reduce API calls
- Manual confirmation is required for repositories without explicit Transformers imports
- The script will not create duplicate PRs for repositories already updated by the user 'xianbao'

## Caution

This script interacts with the Hugging Face Hub API and can create pull requests. Use it carefully and ensure you have the necessary permissions before running the update process.