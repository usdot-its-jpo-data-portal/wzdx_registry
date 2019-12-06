# wzdx_registry

Code for triggering lambda function for ingesting WZDx feed data based on the WZDx Feed Registry Socrata dataset.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

#### Prerequisites for AWS Lambda Deployment

If you plan to deploy the script on AWS Lambda, you need access to an AWS account and be able to assign role(s) to a lambda function. There needs to be a role that is able to execute and invoke lambda functions and perform list/read/write actions to relevant buckets in S3.

#### Prerequisites for Local Deployment

If you plan to deploy the script on your local machine, you need the following:

1. Have access to Python 3.6+. You can check your python version by entering `python --version` and `python3 --version` in command line.
2. Have access to the command line of a machine. If you're using a Mac, the command line can be accessed via the [Terminal](https://support.apple.com/guide/terminal/welcome/mac), which comes with Mac OS. If you're using a PC, the command line can be accessed via the Command Prompt, which comes with Windows, or via [Cygwin64](https://www.cygwin.com/), a suite of open source tools that allow you to run something similar to Linux on Windows.
3. Have your own Free Amazon Web Services account.
	- Create one at http://aws.amazon.com
4.  Obtain Access Keys:
	- On your Amazon account, go to your profile (at the top right)
	- My Security Credentials > Access Keys > Create New Access Key
	- Record the Access Key ID and Secret Access Key ID (you will need them in step 4)
5. Save your AWS credentials in your local machine, using one of the following method:
	- shared credentials file: instructions at https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file.
	- environmental variables: instructions at https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#environment-variables

### Installing locally

1. Download the script by cloning the git repository at https://github.com/usdot-its-jpo-data-portal/wzdx_registry. You can do so by running the following in command line.
`git clone https://github.com/usdot-its-jpo-data-portal/wzdx_registry.git`. If unfamiliar with how to clone a repository, follow the guide at https://help.github.com/en/articles/cloning-a-repository.
2. Navigate into the repository folder by entering `cd wzdx_registry` in command line.
3. Install the required packages by running `pip install -r requirements.txt`.

## Deployment

### Deployment on AWS Lambda

1. To prepare the code package for deployment to AWS Lambda, run `sh package.sh` to build the package. This will create the file `wzdx_trigger_ingest.zip` in the repo's root folder.
2. Create a lambda function in your AWS account "from scratch" with the following setting:
	- Runtime: Python 3.8
	- Permissions: Use an existing role (choose existing role with full lambda access (e.g. policy AWSLambdaFullAccess) and list/read/write permission to your destination s3 bucket)
3. In the configuration view of your lambda function, set the following:
 - In "Designer" section, add a CloudWatch Events trigger
    - Set CloudWatch to trigger at your desired ingestion frequency. Once every 15 minutes is the highest frequency you should set for work zone status ingestion.
 - In "Function code" section, select "Upload a .zip file" and upload the `wzdx_trigger_ingest.zip` file as your "Function Package."
 - In "Environment variables" section, set the following:
    - `DATASET_ID`: ID of the WZDx feed registry Socrata dataset.
      - default set as `69qe-yiui`

    - `LAMBDA_TO_TRIGGER`: Name of the lambda function to trigger.
      - default set as `wzdx_ingest_to_archive`. The code for the `wzdx_ingest_to_archive` can be found at https://github.com/usdot-its-jpo-data-portal/wzdx_sandbox.
    - `SOCRATA_PARAMS`: stringified json object containing Socrata credentials for a user that has write access to the WZDx feed registry. At a minimum, this should include `username`, `password`, `app_token`, and `domain`.
  - In "Basics settings" section, set adequate Memory and Timeout values. Memory of 1664 MB and Timeout value of 10 minutes should be plenty.
4. Make sure to save all of your changes.


## Built With

* [Python 3.6+](https://www.python.org/download/releases/3.0): Python
* [requests](https://pypi.org/project/requests/): package managing HTTP requests
* [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html?id=docs_gateway): AWS API
* [sodapy](https://github.com/xmunoz/sodapy): Python client for the Socrata Open Data API

## Contributing

1. [Fork it](https://github.com/usdot-its-jpo-data-portal/wzdx_registry/fork)
2. Create your feature branch (git checkout -b feature/fooBar)
3. Commit your changes (git commit -am 'Add some fooBar')
4. Push to the branch (git push origin feature/fooBar)
5. Create a new Pull Request

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for general good practices on code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the Apache 2.0 License. - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Thank you to the Department of Transportation for funding to develop this project.

## Code.gov Registration Info

Agency: DOT

Short Description: Code for triggering lambda function for ingesting WZDx feeds based on the WZDx Feed Registry Socrata dataset.

Status: Beta

Tags: transportation, connected vehicles, intelligent transportation systems, python, ITS Sandbox, Socrata, work zone data exchange (WZDx), smart work zone

Labor hours: 0

Contact Name: Brian Brotsos

Contact Phone: (202) 366-9013
