with source as (
    select * from {{ source('raw', 'raw_articles') }}
),

cleaned as (
    select
        row_id                                as article_id,
        trim(title)                           as title,
        trim(text)                            as body_text,
        label                                 as label,  -- 1 = fake, 0 = real
        length(trim(text))                    as body_length_chars,
        case when title is null or trim(title) = '' then true else false end as is_missing_title,
        case when text is null or trim(text) = '' then true else false end as is_missing_body
    from source
    where text is not null  -- drop rows with no article body at all
)

select * from cleaned