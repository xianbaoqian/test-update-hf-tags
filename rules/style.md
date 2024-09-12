# Overall

Please make it super easy for human edition. 
Please document at the top of each file with the algorithm used in this file. What it is for and how it works.
When generating code, please think step by step and explain what you are doing in increasingly complex steps in order to generate great and concise naming and comments.
Comments started with Note! are notes to human editors. Please do not remove them unless they are not appliable or you have a good reason.

# Utils

- Each utility function should have a docstring that describes what the function does and how to use it.
- Each utility function should have a test case that tests the function. The test case should be in the same file as the function. If the test will mutate the Hugging Face Hub, the test can only be enable manually while running the script with a flag which is commonly a repo id or ids separated by commas. When there is no flag, only test the read-only sections. The test can leverage the .env file on the root dir to get the Hugging Face token.
- Each utility function should be grouped based on their usage.
- Each utility function should print out stack trace when an error occurs apart from the nice human readable error message.
