{% set poll_url = url_for("polls", s=poll.season|int, w= poll.week|int, _external=True) %}
{% include 'reddit_results_text.md' %}


Individual ballot information can be found at [{{poll_url}}]({{poll_url}})

Please feel free to discuss the poll results along with individual ballots, but please
be respectful of others' opinions, remain civil, and remember that these are not
professionals, just fans like you.