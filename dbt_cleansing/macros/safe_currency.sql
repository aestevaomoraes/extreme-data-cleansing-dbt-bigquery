{% macro safe_currency(coluna) %}
    case
        when regexp_contains({{ coluna }}, r',\d{1,2}\s*$')
            then safe_cast(
                replace(replace(regexp_replace({{ coluna }}, r'[^0-9,.-]', ''), '.', ''), ',', '.')
                as numeric)
        else safe_cast(regexp_replace({{ coluna }}, r'[^0-9.-]', '') as numeric)
    end
{% endmacro %}