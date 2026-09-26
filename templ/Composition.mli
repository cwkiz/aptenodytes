type ('input, 'output, 'error) t

type ('left, 'right) either =
  | Left of 'left
  | Right of 'right

val make : ('input -> ('output, 'error) result) -> ('input, 'output, 'error) t
val run : ('input, 'output, 'error) t -> 'input -> ('output, 'error) result

val map :
  ('output -> 'mapped) ->
  ('input, 'output, 'error) t ->
  ('input, 'mapped, 'error) t

val contramap :
  ('mapped -> 'input) ->
  ('input, 'output, 'error) t ->
  ('mapped, 'output, 'error) t

val compose :
  ('input, 'middle, 'first_error) t ->
  ('middle, 'output, 'second_error) t ->
  ('input, 'output, ('first_error, 'second_error) either) t
