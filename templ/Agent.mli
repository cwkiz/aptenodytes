type role =
  | System
  | User
  | Assistant
  | Tool

type tool_call = {
  id : string;
  request : Tool.request;
}

type message = {
  role : role;
  content : string;
  tool_name : string option;
  tool_call_id : string option;
  tool_calls : tool_call list;
  tool_response : Tool.response option;
  tool_error : Tool.error option;
}

type completion = {
  content : string;
  tool_calls : tool_call list;
}

type request = {
  messages : message list;
  capabilities : Tool.capability list;
}

type backend_error = string
type backend = (request, completion, backend_error) Composable.t
type client

type error =
  | Provider_error of backend_error
  | Undeclared_tool of string
  | Invalid_tool_call of string
  | Max_tool_rounds of int

type turn = {
  messages : message list;
  answer : string;
}

val message :
  ?tool_name:string ->
  ?tool_call_id:string ->
  ?tool_calls:tool_call list ->
  ?tool_response:Tool.response ->
  ?tool_error:Tool.error ->
  role ->
  string ->
  message

val client : backend -> client
val mock_client : client
val capabilities : Tool.capability list

val turn :
  ?max_tool_rounds:int ->
  client ->
  Tool.adapters ->
  Tool.capability list ->
  message list ->
  string ->
  (turn, error) Stdlib.result

val string_of_error : error -> string
