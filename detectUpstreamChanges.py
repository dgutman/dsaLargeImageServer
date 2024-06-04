import inspect


# import requests

# def compare_with_github(local_filepath, github_url):
#     # Get the file from the GitHub repository
#     response = requests.get(github_url)
#     response.raise_for_status()  # raise exception if invalid response
#     github_file_content = response.text

#     # Read the local file
#     with open(local_filepath, 'r') as local_file:
#         local_file_content = local_file.read()

#     # Compare the contents of the two files
#     return local_file_content == github_file_content


def compare_functions(func1, func2):
    source1 = inspect.getsource(func1)
    source2 = inspect.getsource(func2)
    return source1 == source2
