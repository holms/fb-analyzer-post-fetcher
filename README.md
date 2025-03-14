# FB Analyzer Event Fetcher Service

This service is responsible for fetching events from Facebook pages using the Facebook Graph API. It provides a RESTful API for managing Facebook pages and retrieving events from those pages.

## Features

- Add, retrieve, update, and delete Facebook pages to monitor
- Fetch events from Facebook pages
- Schedule regular event fetching
- Queue events for analysis by the event analyzer service
- RESTful API for integration with other services

## Environment Variables

This service uses environment variables for configuration instead of local environment files. The following environment variables are supported:

### Database Configuration

```
DB_HOST=mysql
DB_PORT=3306
DB_NAME=fb_analyzer
DB_USER=user
DB_PASSWORD=password
DATABASE_URL=mysql://user:password@mysql:3306/fb_analyzer
```

### Redis Configuration

```
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379
```

### Facebook API Credentials

```
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
```

### Service Configuration

```
LOG_LEVEL=info
FETCH_INTERVAL=3600
MAX_PAGES_PER_FETCH=10
MAX_EVENTS_PER_PAGE=100
```

## API Endpoints

### Pages

- `POST /pages/` - Add a new Facebook page to monitor
- `GET /pages/` - Retrieve all monitored Facebook pages
- `GET /pages/{page_id}` - Retrieve a specific Facebook page by ID
- `DELETE /pages/{page_id}` - Delete a Facebook page from monitoring
- `POST /pages/{page_id}/fetch` - Fetch events from a specific Facebook page
- `POST /pages/{page_id}/schedule` - Schedule regular fetching of events from a specific Facebook page
- `DELETE /pages/{page_id}/schedule` - Remove a page from scheduled fetching

### Events

- `GET /events/` - Retrieve events, optionally filtered by page
- `GET /events/{event_id}` - Retrieve a specific event by ID

### Legacy Endpoints (Deprecated)

The following endpoints are maintained for backward compatibility but will be removed in a future version:

- `POST /groups/` - Add a new Facebook group to monitor
- `GET /groups/` - Retrieve all monitored Facebook groups
- `GET /groups/{group_id}` - Retrieve a specific Facebook group by ID
- `DELETE /groups/{group_id}` - Delete a Facebook group from monitoring
- `POST /groups/{group_id}/fetch` - Fetch posts from a specific Facebook group
- `POST /groups/{group_id}/schedule` - Schedule regular fetching of posts from a specific Facebook group
- `GET /posts/` - Retrieve posts, optionally filtered by group
- `GET /posts/{post_id}` - Retrieve a specific post by ID
