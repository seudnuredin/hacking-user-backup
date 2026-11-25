#!/bin/bash

# handle_signal() {
#   echo "Caught signal: $1"
#   # Add your custom logic here (e.g., cleanup)
# #   exit 1
# }

# # Loop through all signals
# for sig in $(kill -l | tr ' ' '\n'); do
#     trap "handle_signal $sig" "$sig"
# done

# Check if at least four arguments are provided
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 status content_measure ffuf_output_file(s)"
    exit 1
fi

if [[ "$2" != "words" && "$2" != "lines" && "$2" != "length" && "$2" != "all" ]]; then
  echo "Invalid content_measure: $2. Must be either words, lines, length, or all for words and lines"
  exit 1
fi

# Assigning arguments
status_or_statuses="$1"

# content_measure="$2"
if [[ "$2" == "all" ]]; then
  content_measures=("words" "lines")
else
  content_measures=("$2")
fi

is_decimate=0

# maximum_occurrence="$3"
if [[ "$3" == "decimate" ]]; then
  is_decimate=1
else
  maximum_occurrence="$3"
fi

shift 3  # Shift past the first 2 arguments
files=("$@")  # Capture all remaining arguments as files

for content_measure in "${content_measures[@]}"; do
    # Loop through each file individually
    for f in "${files[@]}"; do
        echo "Processing file: $f"

        if [ "$is_decimate" -eq 1 ]; then
            maximum_occurrence=$(expr $(wc -l < "$f") / 10 + 10)
        fi

        nprocs=$(nproc)
        total_lines=$(wc -l < "$f")
        for_L=$(( total_lines / nprocs ))

        if [[ "$status_or_statuses" == "all" ]]; then
            statuses=$(parallel -a "$f" --pipepart --block 100M --recend '}\n' -j"$(nproc)" "jq .status" | sort -u | grep -v null | tr '\n' ',' | sed 's/,$//')
        elif [[ "$status_or_statuses" =~ ^[1-5]xx$ ]]; then
            digit="${status_or_statuses:0:1}"
            statuses=$(parallel -a "$f" --pipepart --block 100M --recend '}\n' -j"$(nproc)" "jq .status" |
                       grep -E "^$digit[0-9]{2}$" | sort -u | tr '\n' ',' | sed 's/,$//')
        else
            statuses="$status_or_statuses"
        fi


        # Convert the statuses string into an array
        if [[ "$statuses" == *","* ]]; then
            IFS=',' read -ra STATUSES <<< "$statuses"
        else
            STATUSES=("$statuses")
        fi

        method=$(echo "$f" | sed 's/_/ /g' | awk '{print $2}' | tr -d '\n')
        domain=$(echo "$f" | sed 's/_/ /g' | awk '{print $6}' | rev | cut -d . -f2- | rev | tr -d '\n')

        if [[ "$method" == "path" ]]; then
            method="GET"
            domain=$(echo "$f" | sed 's/_/ /g' | awk '{print $5}' | rev | cut -d . -f2- | rev | tr -d '\n')
        fi


        # Loop through each status for the current file
        for status in "${STATUSES[@]}"; do
            if [[ "$content_measure" == "length" || "$content_measure" == "words" || "$content_measure" == "lines" ]]; then
                # Extract unique content measure values from the file for the given status
                content_values=$(parallel -a "$f" --pipepart --block 100M --recend '}\n' -j$(nproc) "jq -r 'select(.status == $status and .url != null) | .$content_measure' " | sort | uniq -c | sort -nr)

                # Get values within the maximum occurrence threshold
                values_within_threshold=$(echo "$content_values" | \
                    awk -v max="$maximum_occurrence" '$1 <= max {print $2}' | paste -sd '|' -)

                # Get values exceeding the maximum occurrence threshold
                values_exceeding_threshold=$(echo "$content_values" | \
                    awk -v max="$maximum_occurrence" '$1 > max {print $2}' | paste -sd '|' -)

                outfile_within_threshold="./method_and_url_file_within_threshold_${content_measure}.${status}.${maximum_occurrence}.${domain}.txt"
                outfile_exceeding_threshold="./method_and_url_file_exceeding_threshold_${content_measure}.${status}.${maximum_occurrence}.${domain}.txt"

                # Process entries with values within the threshold
                if [[ -n "$values_within_threshold" ]]; then
                    parallel -a "$f" --pipepart --block 100M --recend '}\n' -j"$(nproc)" \
"jq -r --arg method \"$method\" --argjson status $status 'select(.url != null and .status == \$status and (.[\"$content_measure\"] | tostring | test(\"^($values_within_threshold)\$\"))) | 
\"\(\$method | gsub(\" \"; \"\")) \(.url | gsub(\" \"; \"\")) \(.\"content-type\" | gsub(\" \"; \"\"))\"'" \
| anew -q "$outfile_within_threshold"
                fi

                # Process entries with values exceeding the threshold (limit to the first 2 occurrences)
                if [[ -n "$values_exceeding_threshold" ]]; then
                    parallel -a "$f" --pipepart --block 100M --recend '}\n' -j"$(nproc)" \
"jq -r --arg method \"$method\" --argjson status $status 'select(.url != null and .status == \$status and (.[\"$content_measure\"] | tostring | test(\"^($values_exceeding_threshold)\$\"))) | 
\"\(\$method | gsub(\" \"; \"\")) \(.url | gsub(\" \"; \"\")) \(.\"content-type\" | gsub(\" \"; \"\"))\"'" \
| head -n 2 | anew -q "$outfile_exceeding_threshold"
                fi

                # if [[ $status =~ ^3[0-9][0-9]$ ]]; then
                #     parallel -a "$f" \
                #              --pipepart --block 100M --recend '}\n' \
                #              -j$(nproc) \
                #       "jq -r '
                #          # only 3xx
                #          select(.status == $status)
                #          | .redirectlocation as \$r
                #          # if it’s a full URL, keep it, else prefix scheme+host from .url
                #          | ( if (\$r | test(\"^https?://\")) then
                #                \$r
                #              else
                #                ( .url
                #                  | capture(\"^(?<base>https?://[^/]+)\")
                #                  | .base
                #                ) + \$r
                #              end
                #            ) as \$loc
                #          # emit METHOD + final‑location
                #          | [\"$method\", \$loc, .[\"content-type\"]]
                #          | @tsv
                #       '" \
                #     | sort -u -t$'\t' -k2,2 \
                #     | tr '\t' ' ' \
                #     | anew -q "$outfile"

                # fi

            fi
        done
    done
done