---
description: "Implement a sprint from UltraShop sprint specs. Reads the sprint file, checks user stories, and builds all required models, views, URLs, and templates."
agent: "django-developer"
argument-hint: "Sprint number (e.g., 2)"
---
Implement the specified sprint for UltraShop:

1. Read the sprint spec at `Documentation/sprints/sprint-{number}.md`
2. For each story in the sprint, read the full user story from `Documentation/user-stories/`
3. Check what's already implemented in the codebase
4. Implement each story: models → migrations → views → URLs → templates
5. Run `python manage.py check` and `python manage.py makemigrations && python manage.py migrate`
6. Verify the server starts: `python manage.py runserver 8080`

Track progress with the todo list tool — one todo per user story.
