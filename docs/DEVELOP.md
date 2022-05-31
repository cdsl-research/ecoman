# Tips

Formatting

```
flake8 --max-line-length=100 *.py
```

Starting dashboard

```
uvicorn main:app --reload --host 0.0.0.0
```

Docker Build

```
cd $RPOJECT_ROOT
docker build -f crawler/Dockerfile -t crawler .
```