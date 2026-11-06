from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session

app = FastAPI()

# 1. Serve CSS and images from the static directory
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# 2. Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")


# 3. Configure the SQLite database
DATABASE_URL = "sqlite:///./task_manager.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# 4. Create the Task model (database table)
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    completed = Column(Boolean, default=False, nullable=False)


# Create the table if it does not already exist
Base.metadata.create_all(bind=engine)


# 5. Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi.responses import RedirectResponse

@app.get("/")
def home():
    return RedirectResponse(url="/tasks")


# Display all tasks
@app.get("/tasks")
def show_tasks(request: Request, db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.id.desc()).all()

    return templates.TemplateResponse(
        request=request,
        name="tasks.html",
        context={"tasks": tasks}
    )


# Add a new task
@app.post("/tasks")
def add_task(
    title: str = Form(...),
    db: Session = Depends(get_db)
):
    new_task = Task(title=title)

    db.add(new_task)
    db.commit()

    return RedirectResponse(
        url="/tasks",
        status_code=303
    )


# Mark a task as completed
@app.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is not None:
        task.completed = True
        db.commit()

    return RedirectResponse(
        url="/tasks",
        status_code=303
    )


# Delete a task
@app.post("/tasks/{task_id}/delete")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is not None:
        db.delete(task)
        db.commit()

    return RedirectResponse(
        url="/tasks",
        status_code=303
    )
