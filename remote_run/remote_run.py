"""
This script does:

1. Copy local files to remote worker node
2. Run script in the node
3. Fetch output from the node

Q. Why we do not use `rsync`?
=> `rsync` should be installed in both client and server,
    and there are some other libraries required to facilitate the script
    including `sshpass`. Since this script aims to the tasks in which file
    transfer is not a big overhead, we implemented naive file transfer using
    sftp.
"""
import hashlib
import os

import paramiko
from gitignore_parser import parse_gitignore


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class RemoteRunner:
    """
    Remote Task Runner over SSH and SFTP protocols.

    Params
    --------------
    ssh_host: str
        Hostname of the remote server
    ssh_username: str
        Username of the remote server
    ssh_password: str
        Password of the remote server
    ssh_port: int (optional, default=22)
        Port number of the remote server
    remote_work_dir: str (optional, default='./remote-run')
        Directory of the remote worker node to locate files for running the task
    log_level: int (optional, default=2)
        2: print all logs
        1: print only main output of the command
        0: print nothing
    """

    @staticmethod
    def get_workspace(work_dir):
        cur_dir = os.getcwd()
        cur_dir_hash = hashlib.md5(cur_dir.encode()).hexdigest()[0:8]
        dirpath = os.path.join(work_dir, os.path.basename(cur_dir) + '_' + cur_dir_hash).replace(' ', '_')
        return os.path.normpath(dirpath.replace(' ', '_'))

    def __init__(self, ssh_host, ssh_username, ssh_password=None, ssh_port=22,
                 ssh_key_filename=None, remote_work_dir='./remote-run', log_level=2):

        if ssh_password:
            auth_type = 'password'
        elif ssh_key_filename:
            auth_type = 'ssh_key'
        else:
            raise Exception('Either password or ssh_key should be provided')

        self.remote_work_dir = remote_work_dir
        self.log_level = log_level

        self.remote_info = f'{ssh_username}@{ssh_host}:{ssh_port}'
        self._print_log(f'>> Connecting to {self.remote_info} using {auth_type}')

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(
            hostname=ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            key_filename=ssh_key_filename,
        )

    def run(self, command):
        """
        Run command on the remote node

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
        workspace = RemoteRunner.get_workspace(self.remote_work_dir)

        self._print_log(f'>> Using working directory: {workspace}')
        self._copy_files(workspace)

        self._print_log('===============================================')
        exit_code, out, err = self._exec_command(workspace, command)
        return exit_code, out, err

    def close(self):
        """
        Close SSH Client
        """
        self.ssh_client.close()

    def _print_log(self, message, end='\n', log_level=2):
        if self.log_level >= log_level:
            print(message, end=end)

    def _exec_command(self, workspace, command, log_level=1):
        workspace = os.path.normpath(workspace)
        self._print_log(f'[{self.remote_info}:~/{workspace}] $ {command}')
        _, stdout, stderr = self.ssh_client.exec_command(f'cd {workspace} && {command}')

        out, err = '', ''
        for line in stdout:
            self._print_log(BColors.OKBLUE + line + BColors.ENDC, end='', log_level=log_level)
            out += line
        for line in stderr:
            self._print_log(BColors.FAIL + line + BColors.ENDC, end='', log_level=log_level)
            err += line

        exit_code = stdout.channel.recv_exit_status()
        return exit_code, out, err

    def _copy_files(self, workspace):
        self.ssh_client.exec_command(f'[ ! -d "{workspace}" ] && mkdir -p  "{workspace}"')

        sftp_client = self.ssh_client.open_sftp()
        sftp_client.chdir(workspace)
        self._print_log('>> Copy local files to remote')

        if os.path.isfile('.gitignore'):
            should_ignore = parse_gitignore('.gitignore')
        else:
            should_ignore = None

        for dirpath, _, filenames in os.walk('.', topdown=True):
            dirpath = os.path.normpath(dirpath)
            if should_ignore and should_ignore(dirpath):
                continue
            if len(dirpath) >= 4 and dirpath[0:4] == '.git':
                continue

            try:
                remote_file_list = sftp_client.listdir_attr(dirpath)
            except IOError:
                sftp_client.mkdir(dirpath)
                remote_file_list = sftp_client.listdir_attr(dirpath)

            # Get make time of the remote files
            remote_mtimes = {}
            for file_stat in remote_file_list:
                remote_mtimes[file_stat.filename] = file_stat.st_mtime

            for filename in filenames:
                filepath = os.path.normpath(os.path.join(dirpath, filename))

                if should_ignore and should_ignore(filepath):
                    continue

                local_mtime = os.stat(filepath).st_mtime

                # If local mtime greater than remote's, it means file changed.
                if local_mtime > remote_mtimes.get(filename, -1):
                    self._print_log(f'./{filepath}...', end=' ')
                    sftp_client.put(filepath, filepath)
                    self._print_log('uploaded')
                else:
                    self._print_log(f'./{filepath} skipped')

        sftp_client.close()


def remote_run(command, ssh_host, ssh_username,
               ssh_password=None, ssh_port=22,
               ssh_key_filename=None,
               remote_work_dir='./remote-run', log_level=2):

    runner = RemoteRunner(ssh_host, ssh_username, ssh_password, ssh_port,
                          ssh_key_filename, remote_work_dir, log_level)
    out = runner.run(command)
    runner.close()
    return out
