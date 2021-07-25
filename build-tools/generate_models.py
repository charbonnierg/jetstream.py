import logging
from shutil import rmtree
from pathlib import Path
from subprocess import check_call

BUILD_TOOLS_SRC = Path(__file__).parent.resolve(True)
DEFAULT_VERSION = "0.0.24"
DEFAULT_API_VERSION = "v1"


def download_schemas(version: str) -> Path:
    target = f"v{version}.tar.gz"
    archive = BUILD_TOOLS_SRC / f"jsm.go-{version}.tar.gz"
    if not archive.exists():
        url = f"https://github.com/nats-io/jsm.go/archive/refs/tags/{target}"
        cmd = f"wget {url} -O {str(archive)}"
        check_call(cmd, shell=True)
    return archive


def extract_schemas(archive: Path, clean: bool = False) -> Path:
    root_dir = archive.name.replace(".tar.gz", "")
    cmd = f"cd {archive.parent} && tar xzf {str(archive)} {root_dir}/schemas --strip-components=1"
    check_call(cmd, shell=True)
    if clean:
        archive.unlink()
    return archive.parent / "schemas"


def generate_models(schemas_dir: Path, api_version: str, clean: bool = True) -> None:
    for jsonschema in schemas_dir.glob(f"**/{api_version}/*.json"):
        subpackage = (
            BUILD_TOOLS_SRC.parent
            / "src"
            / "jsm"
            / "models"
            / api_version
            / jsonschema.parent.parent.name
        )
        if not (subpackage).exists():
            logging.info(f"Creating subpackage jsm.models.v1.{subpackage.name}")
            subpackage.mkdir(parents=True)
            (subpackage / "__init__.py").touch()
        output_model = subpackage / jsonschema.name.replace(".json", ".py")
        logging.info(
            f"Generating jsm.models.{api_version}.{subpackage.name}.{output_model.stem} module from JSON Schema file: {jsonschema}"
        )
        cmd = f"datamodel-codegen  --input {str(jsonschema)} --input-file-type jsonschema --output {str(output_model)}"
        check_call(cmd, shell=True)
    if clean:
        logging.info(f"Removing directory {schemas_dir}")
        rmtree(schemas_dir)


if __name__ == "__main__":
    import os

    JSM_VERSION = os.environ.get("JSM_VERSION", DEFAULT_VERSION)
    JS_API_VERSION = os.environ.get("JS_API_VERSION", DEFAULT_API_VERSION)
    CLEAN_SCHEMAS = os.environ.get("CLEAN_SCHEMAS", "True")
    if CLEAN_SCHEMAS.lower() in ("1", "y", "yes", "true"):
        clean_schemas = True
    else:
        clean_schemas = False
    logging.basicConfig(level=logging.INFO)
    archive = download_schemas(JSM_VERSION)
    schemas_root = extract_schemas(archive, clean=True)
    generate_models(schemas_root, JS_API_VERSION, clean=clean_schemas)
