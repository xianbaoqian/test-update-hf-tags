from huggingface_hub import list_models
import csv

import yaml

# Note! sort can be likes7d, likes30d , downloads
def get_no_library_repos(sort="likes7d", limit=2000):
    popular_models = list(list_models(sort=sort, limit=limit))

    no_library_repos = []
    for model in popular_models:
        # check if attribut library
        if not model.library_name:
            no_library_repos.append(model.id)

    return no_library_repos

if __name__ == "__main__":
    no_library_repos_ids = get_no_library_repos(sort="likes30d")
    with open("no_library_repos.yaml", "w") as f:
        yaml.dump(no_library_repos_ids, f)