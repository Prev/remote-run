"""
Usage: python -m remote_run.cli "pwd" root:1234@10.0.0.1:30022
"""
import sys
import fire
import getpass

from . import remote_run, remote_run_docker

def remote_run_cli(
        command,
        ssh_url=None,
        host=None,
        port=None,
        username=None,
        password=None,
        key_filename=None,
        remote_work_dir='./remote-run',
        docker_image=None,
        docker_args='',
        nvidia_docker=False,
    ):

    if not ssh_url and (not host or not username):
        print('Usage: remote-run COMMAND USERNAME:PASSWORD@HOST \n'
              '       or \n'
              '       remote-run COMMAND --host HOST --username USERNAME --password PASSWORD')
        sys.exit(-1)

    if ssh_url:
        userpart, hostpart = ssh_url.split('@')
        userpart = userpart.split(':')
        hostpart = hostpart.split(':')

        if not username:
            if len(userpart) == 2 and not password:
                username, password = userpart
            else:
                username = userpart[0]

        if not host:
            if len(hostpart) == 2 and not port:
                host, port = hostpart
            else:
                host = hostpart[0]

    if not port:
        port = 22

    if not password and not key_filename:
        print('Neither `password` nor `key_filename` was provided.')
        password = getpass.getpass('Enter password: ')

    if docker_image:
        remote_run_docker(
            command=command,
            docker_image=docker_image,
            ssh_host=host,
            ssh_username=username,
            ssh_password=password,
            ssh_port=port,
            ssh_key_filename=key_filename,
            remote_work_dir=remote_work_dir,
            nvidia_docker=nvidia_docker,
            docker_args=docker_args,
        )
    else:
        remote_run(
            command=command,
            ssh_host=host,
            ssh_username=username,
            ssh_password=password,
            ssh_port=port,
            ssh_key_filename=key_filename,
            remote_work_dir=remote_work_dir,
        )


def main():
    fire.Fire(remote_run_cli)


if __name__ == '__main__':
    main()
