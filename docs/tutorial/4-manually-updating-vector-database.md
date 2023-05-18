# Tutorial 4: Manually Updating the Django Vector Database

Introduction: In our [previous tutorial][previous-tutorial], we explored how to automatically update the vector database. In this tutorial, we will learn how to manually update the vector database. This can be particularly useful when you want to add items to the database.

VectorDB offers two utility methods for adding items to the database: `vectordb.add_instance` and `vectordb.add_text`. It is important to note that when adding an instance, you need to provide the `get_vectordb_text` method and an optional `get_vectordb_metadata` method.

## Adding Model Instances

To manually add a django model instance to the vector database, you can use the following code:

```python
post1 = models.create(title="post1", description="post1 description", user=user1) # provide a valid user

# Add the instance to the vector database
vectordb.add_instance(post1)
```

## Adding Text to the Model

If you want to add text to the database, you can use the `vectordb.add_text()` method:

```python
vectordb.add_text(text="Hello text", id=3, metadata={"user_id": 1})
```

Both the `text` and `id` parameters are required when using this method. Additionally, the `id` must be unique; otherwise, an error will occur. The `metadata` parameter can be set to `None` or any valid JSON.

By following these steps, you can manually update the Django vector database with new instances and text. This flexibility allows you to have more control over the data in our database and ensures that you can add items that may not be automatically included.

## Summary

In this tutorial, we learned how to manually update the Django vector database by adding model instances and text. We explored the utility methods `vectordb.add_instance` and `vectordb.add_text`, which allow for greater control over the data in the database. This flexibility is particularly useful when you want to add items that may not be automatically included in the database.

In the [next tutorial][next-tutorial], we will dive into performing vector similarity searches using the Django vector database. This powerful feature will enable you to find similar items in our database based on their vector representations, further enhancing the capabilities of our Django application. Stay tuned!

[previous-tutorial]: 3-automatically-updating-vector-database.md
[next-tutorial]: 5-vector-search.md
