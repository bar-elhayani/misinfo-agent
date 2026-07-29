with articles as (
    select * from {{ ref('stg_articles') }}
),

enriched as (
    select
        article_id,
        title,
        body_text,
        label,
        body_length_chars,
        is_missing_title,
        is_missing_body,

        case
            when title is null then 0
            else array_length(string_split(trim(title), ' '))
        end                                                          as title_word_count,

        case
            when body_text is null then 0
            else array_length(string_split(trim(body_text), ' '))
        end                                                          as body_word_count,

        case
            when body_length_chars = 0 or body_length_chars is null then 0
            else round(length(coalesce(title, ''))::double / body_length_chars, 4)
        end                                                           as title_to_body_ratio,

        case
            when title is null then 0
            else length(title) - length(replace(title, '!', ''))
        end                                                          as title_exclamation_count,

        case
            when title is null then false
            else title like '%?%'
        end                                                          as title_question_mark_flag,

        case
            when title is null or length(regexp_replace(title, '[^A-Za-z]', '', 'g')) = 0 then 0.0
            else round(
                length(regexp_replace(title, '[^A-Z]', '', 'g'))::double
                / length(regexp_replace(title, '[^A-Za-z]', '', 'g')),
                4
            )
        end                                                           as title_upper_ratio

    from articles
),

final as (
    select
        *,
        case
            when title_upper_ratio >= 0.5
                 or title_exclamation_count >= 2
                 or (title_question_mark_flag and title_upper_ratio >= 0.3)
            then true
            else false
        end as is_clickbait_style
    from enriched
)

select * from final
