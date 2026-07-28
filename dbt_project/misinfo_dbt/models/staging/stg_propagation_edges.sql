with source as (
    select * from {{ source('raw', 'raw_propagation_edges') }}
),

cleaned as (
    select
        graph_id,
        source_node,
        target_node
    from source
    where source_node is not null
      and target_node is not null
)

select * from cleaned