"""
Run the tasks in the docker container on the remote worker
"""
import os

from .remote_run import RemoteRunner

class RemoteRunnerWithDocker(RemoteRunner):

    def __init__(self, docker_image, ssh_host, ssh_username,
                 ssh_password, ssh_port=22, ssh_key_filename=None,
                 remote_work_dir='./remote-run',
                 docker_args='', nvidia_docker=False,
                 log_level=2):

        super().__init__(ssh_host, ssh_username, ssh_password, ssh_port,
                         ssh_key_filename, remote_work_dir, log_level)

        self.docker_image = docker_image
        self.docker_args = docker_args
        self.nvidia_docker = nvidia_docker

    def run(self, command):
        """
        Run command in the docker container on remote node

        Params
        -------------
        command: str
            Command to execute

        Returns
        -------------
        exit_code: int
            Process exit code
        out: str
            Concatenated Stdout
        err: str
            Concatenated Stderr
        """
        command = command.replace('\r', ' ').replace('\n', ' ')
        workspace = RemoteRunner.get_workspace(self.remote_work_dir)
        cur_proj_dirname = os.path.basename(workspace)

        self._print_log(f'>> Using working directory: {workspace}')
        self._copy_files(workspace)

        # Get current directory name + hash
        dockerfile_name = f'{cur_proj_dirname}.Dockerfile'
        docker_image_name = f'remote_run_{cur_proj_dirname}'.lower()

        # Create Dockerfile
        dockerfile_content = self._generate_dockerfile(cur_proj_dirname, command)
        self._exec_command(
            workspace=self.remote_work_dir,
            command=f'echo "{dockerfile_content}" > {dockerfile_name}',
            log_level=2,
        )

        # Build Docker image
        self._exec_command(
            workspace=self.remote_work_dir,
            command=f'docker build -f {dockerfile_name} -t {docker_image_name} .',
            log_level=2,
        )

        # Run Docker
        docker_bin = 'nvidia-docker' if self.nvidia_docker else 'docker'
        docker_run_command = f'{docker_bin} run --rm {self.docker_args} {docker_image_name}'

        exit_code, out, err = self._exec_command(
            workspace=workspace,
            command=docker_run_command,
            log_level=1,
        )

        # Remove image
        self._exec_command(
            workspace=workspace,
            command=f'docker rmi -f {docker_image_name}',
            log_level=2,
        )
        return exit_code, out, err

    def _generate_dockerfile(self, dirname, command):
        return f'FROM {self.docker_image}\n' \
            f'COPY {dirname} /usr/src/{dirname}/\n' \
            f'WORKDIR /usr/src/{dirname}/\n' \
            f'CMD {command}\n'


def remote_run_docker(command, docker_image, ssh_host, ssh_username,
                      ssh_password, ssh_port=22, ssh_key_filename=None,
                      remote_work_dir='./remote-run',
                      docker_args='', nvidia_docker=False,
                      log_level=2):

    runner = RemoteRunnerWithDocker(
        docker_image, ssh_host, ssh_username, ssh_password, ssh_port,
        ssh_key_filename, remote_work_dir, docker_args, nvidia_docker, log_level)
    out = runner.run(command)
    runner.close()
    return out
