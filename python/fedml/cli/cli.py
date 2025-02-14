import os
import platform

import click
import shutil


@click.group()
def cli():
    pass


@cli.command(
    "login", help="Login to MLOps platform (open.fedml.ai)"
)
@click.argument("userid", nargs=-1)
@click.option(
    "--version",
    "-v",
    type=str,
    default="release",
    help="account id at open.fedml.ai MLOps platform",
)
def mlops_login(userid, version):
    account_id = userid[0]
    click.echo("Argument for account Id: " + str(account_id))
    click.echo("Argument for version: " + str(version))

    sys_name = platform.system()
    if sys_name == "Windows":
        click.echo("Login into the FedML MLOps platform on the Windows platform will be coming soon. Please stay tuned.")
        exit(-1)

    cur_dir = os.path.dirname(__file__)
    run_shell = os.path.join(cur_dir, "edge_deployment", "run.sh") + " " + account_id + " " + version
    os.system(run_shell)


@cli.command(
    "build", help="Build packages for MLOps platform (open.fedml.ai)"
)
@click.option(
    "--type",
    "-t",
    type=str,
    default="client",
    help="client or server? (value: client; server)",
)
@click.option(
    "--source_folder", "-sf", type=str, default="./", help="the source code folder path"
)
@click.option(
    "--entry_point",
    "-ep",
    type=str,
    default="./",
    help="the entry point of the source code",
)
@click.option(
    "--config_folder", "-cf", type=str, default="./", help="the config folder path"
)
@click.option(
    "--dest_folder", "-df", type=str, default="./", help="the destination package folder path"
)
def mlops_build(type, source_folder, entry_point, config_folder, dest_folder):
    click.echo("Argument for type: " + type)
    click.echo("Argument for source folder: " + source_folder)
    click.echo("Argument for entry point: " + entry_point)
    click.echo("Argument for config folder: " + config_folder)
    click.echo("Argument for destination package folder: " + dest_folder)

    if type == "client" or type == "server":
        click.echo("Now, you are building the fedml packages which will be used in the MLOps "
                   "platform.")
        click.echo("The packages will be used for client training and server aggregation.")
        click.echo("When the building process is completed, you will find the packages in the directory as follows: "
                   + os.path.join(dest_folder, "dist-packages") + ".")
        click.echo("Then you may upload the packages on the configuration page in the MLOps platform to start the "
                   "federated learning flow.")
        click.echo("Building...")
    else:
        click.echo("You should specify the type argument value as client or server.")
        exit(-1)

    if type == "client":
        build_mlops_package(source_folder, entry_point, config_folder, dest_folder,
                            "fedml-client", "client-package", "${FEDSYS.CLIENT_INDEX}")
        click.echo("You have finished all building process. ")
        click.echo("Now you may use " + os.path.join(dest_folder, "client-package.zip") + " to start your federated "
                   "learning run.")
    elif type == "server":
        build_mlops_package(source_folder, entry_point, config_folder, dest_folder,
                            "fedml-server", "server-package", "0")

        click.echo("You have finished all building process. ")
        click.echo("Now you may use " + os.path.join(dest_folder, "server-package.zip") + " to start your federated "
                   "learning run.")


def build_mlops_package(source_folder, entry_point, config_folder, dest_folder,
                        mlops_root_dir_name, mlops_package_name, rank):
    mlops_src = source_folder
    mlops_src_entry = entry_point
    mlops_conf = config_folder
    cur_dir = os.path.dirname(__file__)
    mlops_root_dir = os.path.join(cur_dir, "build-package", "mlops-core", mlops_root_dir_name)
    package_dir = os.path.join(mlops_root_dir, mlops_package_name)
    fedml_dir = os.path.join(package_dir, "fedml")
    mlops_dest = fedml_dir
    mlops_dest_conf = os.path.join(fedml_dir, "config")
    mlops_pkg_conf = os.path.join(package_dir, "conf", "fedml.yaml")
    mlops_dest_entry = os.path.join("fedml", mlops_src_entry)
    mlops_package_file_name = mlops_package_name + ".zip"
    dist_package_dir = os.path.join(dest_folder, "dist-packages")
    dist_package_file = os.path.join(dist_package_dir, mlops_package_file_name)

    shutil.rmtree(mlops_dest, ignore_errors=True)
    shutil.copytree(mlops_src, mlops_dest, copy_function=shutil.copy)
    shutil.copytree(mlops_conf, mlops_dest_conf, copy_function=shutil.copy)
    os.remove(os.path.join(mlops_dest_conf, "mqtt_config.yaml"))
    os.remove(os.path.join(mlops_dest_conf, "s3_config.yaml"))

    local_mlops_package = os.path.join(mlops_root_dir, mlops_package_file_name)
    if os.path.exists(local_mlops_package):
        os.remove(os.path.join(mlops_root_dir, mlops_package_file_name))
    mlops_archive_name = os.path.join(mlops_root_dir, mlops_package_name)
    shutil.make_archive(mlops_archive_name, 'zip', root_dir=mlops_root_dir, base_dir=mlops_package_name)
    if not os.path.exists(dist_package_dir):
        os.makedirs(dist_package_dir)
    if os.path.exists(dist_package_file):
        os.remove(dist_package_file)
    mlops_archive_zip_file = mlops_archive_name + ".zip"
    if os.path.exists(mlops_archive_zip_file):
        shutil.move(mlops_archive_zip_file, dist_package_file)

    mlops_pkg_conf_file = open(mlops_pkg_conf, mode="w")
    mlops_pkg_conf_file.writelines(["entry_config: \n",
                                    "  entry_file: " + mlops_dest_entry + "\n",
                                    "  conf_file: " + os.path.join("config", "fedml_config.yaml") + "\n"
                                    "dynamic_args:\n",
                                    "  rank: " + rank + "\n",
                                    "  run_id: ${FEDSYS.RUN_ID}\n",
                                    # "  data_cache_dir: ${FEDSYS.PRIVATE_LOCAL_DATA}\n",
                                    "  data_cache_dir: /fedml/fedml-package/fedml/data\n",
                                    "  mqtt_config_path: /fedml/fedml_config/mqtt_config.yaml\n",
                                    "  s3_config_path: /fedml/fedml_config/s3_config.yaml\n",
                                    "  log_file_dir: /fedml/fedml-package/fedml/data\n",
                                    "  log_server_url: ${FEDSYS.LOG_SERVER_URL}\n",
                                    "  client_id_list: ${FEDSYS.CLIENT_ID_LIST}\n",
                                    "  client_objects: ${FEDSYS.CLIENT_OBJECT_LIST}\n",
                                    "  is_using_local_data: ${FEDSYS.IS_USING_LOCAL_DATA}\n",
                                    "  synthetic_data_url: ${FEDSYS.SYNTHETIC_DATA_URL}\n",
                                    "  client_num_in_total: ${FEDSYS.CLIENT_NUM}\n"])
    mlops_pkg_conf_file.flush()
    mlops_pkg_conf_file.close()


# TODO:
# Maybe not be supported as follows
# fedml mlops --action deploy
# fedml mlops --action logout
# fedml mlops --action on
# fedml mlops --action off
# fedml mlops --action clean
# fedml mlops --action exit
# So we should do as follows
# fedml mlops-deploy
# fedml mlops-logout
# fedml mlops-on
# fedml mlops-off
# fedml mlops-clean
# fedml mlops-exit


if __name__ == "__main__":
    cli()
