{%- for release in releases -%}
# {{ release.version }}{% if not release.is_released %} (Unreleased){% endif %}
{% for section in release.sections %}
**{{ section.title }}**

{% for change in section.changes | reverse -%}
- {% if change.scope %}{{ change.scope }}: {% endif %}{{ change.description }}
{% endfor %}{% endfor %}
{% endfor %}
