with source as (
    select * from {{ source('raw', 'raw_propagation_graphs') }}
),

cleaned as (
    select
        graph_id,
        source_dataset,
        split,
        num_nodes,
        label,  -- 1 = fake, 0 = real
        case when num_nodes <= 1 then true else false end as has_no_spread  -- article + no retweets at all
    from source
)

select * from cleaned