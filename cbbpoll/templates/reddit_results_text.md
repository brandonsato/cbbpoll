Rank||Team (First Place Votes)|Score
:--:|:--:|:---|:---
{% set prev_score = -1 -%}
{%- for result in results -%}
  {% set team = teams.get(result[0]) %}
  {%- if team.short_name %}{% set name = team.short_name %}{% else %}{% set name = team.full_name %}{% endif -%}
    {%- if loop.index < 26 -%}
      {%- if result[1][0] == prev_score -%}
        {%- set rank = prev_rank -%}
      {%- else -%}
        {%- set rank = loop.index -%}
      {%- endif -%}
    {%- set prev_rank = rank -%}
    {%- set prev_score = result[1][0] -%}
#{{rank}}|{%- if team.flair -%}[](/{{team.flair}}){%-endif-%}|{{name}} {% if result[1][1] -%}({{result[1][1]}}){%-endif %}|{{ result[1][0]}}
{% elif loop.index == 26 %}
Others Receiving Votes: {{name}}({{result[1][0]}}){%- else -%}, {{name}}({{result[1][0]}})
{%- endif -%}
{% endfor %}