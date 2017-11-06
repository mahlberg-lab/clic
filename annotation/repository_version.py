import os.path
import json
import sys

def repository_version(repo, version):
    extra_data_file = os.path.join(os.path.dirname(__file__), '..', 'annotationOutput', 'extra_data.json')

    if not os.path.exists(extra_data_file):
        raise ValueError("Cannot find extra_data.json, looked in %s" % extra_data_file)

    with open(extra_data_file, 'rb') as f:
        extra_data = json.load(f)

    if 'repository_versions' not in extra_data:
        extra_data['repository_versions'] = {}

    extra_data['repository_versions'][repo] = version
    with open(extra_data_file, 'wb') as f:
        json.dump(extra_data, f, indent=4, sort_keys=True)


if __name__ == "__main__":
    repository_version(sys.argv[1], sys.argv[2])
