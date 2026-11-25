awk -v names="$(paste -sd' ' graphql_names.txt)" '
BEGIN {
  n = split(names, arr, " ")
  in_block = 0
  brace_count = 0
  parantheses_count = 0
}
{
  i = 1
  brace_count = 0
  parantheses_count = 0
  while (i <= length($0)) {
    c = substr($0, i, 1)

    if (in_block == 0) {
      found = 0
      for (j = 1; j <= n; j++) {
        nm = arr[j]
        len_query = length("query " nm)
        len_mutation = length("mutation " nm)

        if (substr($0, i, len_query) == "query " nm) {
          found = len_query
          break
        } else if (substr($0, i, len_mutation) == "mutation " nm) {
          found = len_mutation
          break
        }
      }
      if (found) {
        in_block = 1
        brace_count = 0
        parantheses_count = 0
        brace_count_prev = 0
        rest = substr($0, i)
        i = 1  # reset i to start scanning rest
        $0 = rest  # replace the line to rest
        continue
      }
    }

    if (in_block == 1) {
      printf "%s", c
      if (c == "(") parantheses_count++
      if (c == ")") parantheses_count--
      if (c == "{" && parantheses_count == 0) brace_count++
      if (c == "}" && parantheses_count == 0) brace_count--

      if (brace_count == 0 && brace_count_prev > 0) {
        printf "\n"  # separate queries
        in_block = 0  # done with one block, search again
      }
      brace_count_prev = brace_count
    }

    i++
  }
}
' graphql_in_blob.txt