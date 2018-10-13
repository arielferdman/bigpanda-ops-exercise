# bigpanda-ops-exercise
An exercise for a dev ops interview

python version = 3.7.0

To deploy the app localy:

Clone the repository:
`$ git clone git@github.com:arielferdman/bigpanda-ops-exercise.git`

Run the python deploy script:
`$ python3.7 deploy.py`

Log file for the deploy process (will be in the base dir of the repository):
`$ tail -f deploy.log`

The deploy script uses docker-compose so docker and docker-compose are prerequisites for running it.
