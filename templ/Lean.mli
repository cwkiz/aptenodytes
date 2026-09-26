type request =
  | Check of { source : string }

type result = {
  accepted : bool;
  exit_code : int;
  stdout : string;
  stderr : string;
}

type executable =
  | Lake
  | Elan

type invocation = {
  executable : executable;
  arguments : string list;
  working_directory : string option;
  stdin : string;
}

type runtime =
  | Lake_runtime
  | Elan_runtime of { toolchain : string }

type client
type error = Subprocess.error

val client :
  ?working_directory:string ->
  runtime:runtime ->
  lake:invocation Subprocess.t ->
  elan:invocation Subprocess.t ->
  unit ->
  client

val run : client -> request -> (result, error) Stdlib.result

val tool :
  client ->
  (request, result, error) Composable.t

val unconfigured_client : client
