# Task Remote Runner

A script file that performs:

1. Copy local files to remote worker node
2. Run script in the remote worker
3. Fetch output from the remote worker

over SSH and SFTP protocols.

## Getting Started

### How to install

```bash
$ pip install git+https://github.com/Prev/remote-run.git
```

### CLI Usage

```bash
$ remote-run "ls -al" ubuntu@10.0.0.1:22

# which is equivalent to
$ remote-run "ls -al" --host "10.0.0.1" --username "ubuntu" --port 22
```


### Providing password or ssh key

Using password:

```bash
$ remote-run "ls -al" root:1234@10.0.0.1

# which is equivalent to
$ remote-run "ls -al" \
    --host "10.0.0.1" \
    --username "root" \
    --password "1234" \
```

Using ssh key:

```bash
$ remote-run "ls -al" root@10.0.0.1 --key-filename 'key.pem'
```

### Using in Python

```python
from remote_run import remote_run

out, err = remote_run(
    command='python main.py',
    ssh_host='10.0.0.1',
    ssh_username='root',
    ssh_password='1234',
    ssh_port=22,
)
print(out)
```

## Remote runner with Docker

Running the task in a docker container on the remote node is also available.
The script performs:

1. Copy local files to remote worker node
2. Build docker image with the files
3. Run docker container on the node
4. Fetch output from the node
5. Remove docker container and the image

(Docker engine should be installed in the worker node)

### CLI Usage

```bash
$ remote-run "python foo.py" root:1234@10.0.0.1:22 --docker-image "python:3.7"
```

Using custom arguments:

```bash
$ remote-run "python train.py" \
    --host "10.0.0.1" \
    --port 22 \
    --username "root" \
    --password "1234" \
    --docker-image "pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime" \
    --docker-args "'--shm-size 11g'" \
    --nvidia-docker \
```

### Using in Python

```python
from remote_run import remote_run

out, err = remote_run_docker(
    command='python train.py',
    ssh_host='10.0.0.1',
    ssh_username='root',
    ssh_password='1234',
    ssh_port=22,
    docker_image='pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime',
    docker_args='--shm-size 11g',
    nvidia_docker=True,
    log_level=0,
)
print(out)
```
