We can use the huggingface_hub library to get the metadata from the model card.

```python
from huggingface_hub import hf_hub_download

model_id = "meta-llama/Meta-Llama-3.1-70B-Instruct"
file_path = hf_hub_download(repo_id=model_id, filename="README.md")
```

or we can use RepoCard to get the metadata.

```python
from huggingface_hub import RepoCard

model_id = "meta-llama/Meta-Llama-3.1-70B-Instruct"
repo_card = RepoCard.load(model_id)
metadata = repo_card.data.to_dict()
```

We can use the `pyyaml` library to parse the YAML metadata from the model card.

```python
import yaml
metadata = yaml.safe_load(repo_card.data.to_yaml())
```

To add a tag, we need to add the tag to the metadata.

```python
metadata["library_name"] = "transformers"
```

To save the metadata, and update the model card, we can use the `push_to_hub` method.

```python
repo_card.push_to_hub(
    repo_id=model_id,
    commit_message="Update metadata",
    create_pr=True
)
```

Note that in order to raise a PR you need to have a token with read access to external repo and the right to access discussions of external repo.