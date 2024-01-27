# GlassDollar Crawler

This project is a crawler that scrapes corporates and their startup partners data from [GlassDollar](https://ranking.glassdollar.com/). It captures key details about enterprises and their startup partners, storing the data in JSON format. The crawler uses Celery for distributed task processing to efficiently handle multiple scraping jobs in parallel. After scraping, it employs NLP techniques for company similarity analysis and provides the functionality as a service through a FastAPI server.


## Features

- Scrapes corporate and startup data from GlassDollar.
- Processes scraping tasks in parallel using Celery.
- Analyzes company similarities based on description, geographical closeness, and closeness of startup partnerships.
- Offers a FastAPI server to access the results as a service.
- Utilizes RabbitMQ for message brokering and Docker for containerization.
- Deployable in a Docker container defined in `docker-compose.yml`.


## Getting Started

### Prerequisites

Before running the project, make sure you have Docker and Docker Compose installed on your system.

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Mutti499/entrapeer_case.git
cd entrapeer_case
```

2. Build and run the Docker containers:

```bash
sudo docker compose up --build
```

This command will start all the services defined in `docker-compose.yml`, including RabbitMQ, Redis, Celery workers, and the FastAPI server.


3. To close the services, press `Ctrl+C` and run:

```bash
docker compose down
```

### Usage

To initiate the scraping process, navigate to:

```
http://localhost:8000/scraper
```

This will start the scraping tasks and once completed, the data will be available through the FastAPI endpoints.

### API Endpoints

- `/` - Returns a instruction message for using the API.
- `/scraper` - Initiates the scraping process and returns the status of the operation. This endpoint returns the companies that are scraped from the query when it is finished. Additionally, it writes the result to company_details.json.
You can reach the file with the following command:
```
 cat company_details.json
```
If you having trouble to reach the file, look at the "Extra commands for eliminating the problems" section at the end.

  Important note: This endpoint contains both asynchronous and synchronous operations. Deciding which corporates to scrape and fetching them from the query are done synchronously since it takes a short time. Scraping tasks are executed asynchronously using Celery since it takes time.

- `/grouper` - Groups the scraped companies based on their similarities and returns the results. Also written synchronously since it takes a short time ( Option to turn it into an asynchronous task is available in the code). It writes the created clusters to clustered_companies.json. Also, it updates company_details.json with the cluster information. 
 

You can reach the file with the following command:
```
 cat clustered_companies.json
```
If you having trouble to reach the file, look at the "Extra commands for eliminating the problems" section at the end.

## Built With

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used for the API server.
- [Celery](https://docs.celeryproject.org/en/stable/index.html) - Asynchronous task queue/job queue.
- [RabbitMQ](https://www.rabbitmq.com/) - Message broker for Celery.
- [Docker](https://www.docker.com/) - Container platform used to containerize the application.


## From

- **Mustafa Atak** - *Idea and coding*
- **ChatGPT** - *Redundant Work Asistant for jobs like documentation*


## Final Note

This project is part of the Entrapeer Case Study. It is not optimized in terms of performance and code quality, as the focus was on completing it quickly.


### Extra commands for eliminating the problems

#### Reaching to the files
To reach files you need to access container shell. To do that, run the following command:
```
sudo docker exec -it <container_id> /bin/bash
```

To find the container id, run the following command:
```
docker ps
```
Choose the container id with the image name case-web
Once you are in the container shell, you can reach the files with the following commands:
```
cat company_details.json
cat clustered_companies.json
```


#### Solving RabbitMQ is using the port error

controlling use of port:
```
 sudo lsof -i :5672
 ```
close the service in order to use the port:
```
 sudo systemctl stop <service_name> (probably rabbitmq-server)
 ```
start the service again for development: 
```
 sudo systemctl start <service_name> (probably rabbitmq-server)

```