# Test Code Creation Guide

## Overview

This document explains the basic procedures and methods for creating test code in **ckanext-feedback**. It focuses particularly on how to use fixtures defined in `conftest.py` and how to execute database tests.  
To execute test code, please refer to [README Testing](../../README.md#testing).

## Table of Contents

1. [Preparing the Test Environment](#preparing-the-test-environment)
2. [How to Use Fixtures](#how-to-use-fixtures)
3. [Executing Database Tests](#executing-database-tests)
4. [Test Code Writing Patterns](#test-code-writing-patterns)
5. [Common Usage Examples](#common-usage-examples)

## Preparing the Test Environment

### Required Dependencies

The following dependencies are required to execute tests:

- pytest
- pytest-freezegun (for time-fixed testing)
- CKAN test helpers

### Test Directory Structure

```
ckanext-feedback/
├── ckanext/feedback/tests/
│   ├── conftest.py                    # Common fixture definitions
│   ├── services/
│   │   └── admin/
│   │       └── test_utilization.py    # Test file example
│   └── ...
```

## How to Use Fixtures

### Basic Fixtures

The following fixtures are defined in `conftest.py`:

- `user`: Test user
- `sysadmin`: System administrator user
- `organization`: Test organization
- `dataset`: Test dataset
- `resource`: Test resource
- `utilization`: Test utilization
- `resource_comment`: Test resource comment
- `download_summary`: Test download summary

### How to Use Fixtures

Example: Using temporary resource and utilization in a test
```python
def test_example(self, resource, utilization):
    # resource and utilization fixtures are automatically available
    assert resource['id'] == utilization.resource_id
    assert utilization.title == 'test_title'
```

### Fixture Dependencies

Fixture dependencies are automatically resolved:

Example: utilization fixture
```python
@pytest.fixture(scope='function')
def utilization(user, resource):  # Depends on user and resource
    # user and resource fixtures are executed first
    utilization = Utilization(
        id=str(uuid.uuid4()),
        resource_id=resource['id'],  # Use resource fixture value
        approval_user_id=user['id'], # Use user fixture value
        # ... other attributes
    )
    session.add(utilization)
    session.flush()
    return utilization
```

## Executing Database Tests

### @pytest.mark.db_test Decorator

Tests that use the database must be decorated with `@pytest.mark.db_test`:

Example: Adding decorator to tests that manipulate the database
```python
@pytest.mark.db_test
def test_database_operation(self, resource, utilization):
    # Test including database operations
    pass
```

### Database Test Operation Mechanism

#### 1. At Test Start

```python
@pytest.fixture(autouse=True)
def reset_transaction(request):
    if request.node.get_closest_marker('db_test'):
        reset_db()                    # Reset database
        model.repo.init_db()          # Initialize database
        engine = model.meta.engine
        create_utilization_tables(engine)    # Create necessary tables
        create_resource_tables(engine)
        create_download_tables(engine)
        
        yield
        
        session.rollback()            # Rollback after test completion
        reset_db()                    # Clean up database
```

#### 2. During Test Execution

```python
@pytest.mark.db_test
def test_refresh_utilization_summary(self, resource, utilization):
    resource_ids = [resource['id']]
    
    # Execute database operations
    utilization_service.refresh_utilization_summary(resource_ids)
    
    # Commit changes (possible within test)
    session.commit()
    
    # Get and verify data after commit
    utilization_summary = get_registered_utilization_summary(resource['id'])
    assert utilization_summary.utilization == 1
```

#### 3. At Test Completion

- All changes during the test are rolled back with `session.rollback()`
- Database is cleaned up with `reset_db()`
- Ready for the next test

## Test Code Writing Patterns

### Basic Test Structure

```python
class TestUtilizationService:
    @pytest.mark.db_test
    def test_method_name(self, resource, utilization):
        # 1. Prepare test data (automated with fixtures)
        # 2. Execute method under test
        # 3. Verify results
        # 4. session.commit() if necessary
        pass
```

### Time-fixed Tests

```python
@pytest.mark.freeze_time(datetime(2024, 1, 1, 15, 0, 0))
def test_time_dependent_function(self, resource, utilization):
    # Execute test at fixed time
    result = time_dependent_function()
    assert result.created == datetime(2024, 1, 1, 15, 0, 0)
```

### Combining Multiple Fixtures

```python
def test_complex_scenario(self, user, resource, utilization, resource_comment):
    # Test complex scenarios by combining multiple fixtures
    assert resource_comment.resource_id == resource['id']
    assert utilization.resource_id == resource['id']
    assert utilization.approval_user_id == user['id']
```

## Common Usage Examples

### 1. Testing Basic CRUD Operations

```python
@pytest.mark.db_test
def test_create_utilization(self, resource, user):
    # Create new utilization
    utilization_data = {
        'resource_id': resource['id'],
        'title': 'New Utilization',
        'url': 'http://example.com',
        'description': 'Test description'
    }
    
    result = utilization_service.create(utilization_data)
    session.commit()
    
    # Verify creation result
    assert result.title == 'New Utilization'
    assert result.resource_id == resource['id']
```

### 2. Testing Aggregation Processing

```python
@pytest.mark.db_test
def test_utilization_summary_calculation(self, resource, utilization):
    # Create multiple utilizations
    create_multiple_utilizations(resource['id'])
    session.commit()
    
    # Execute aggregation processing
    summary = utilization_service.calculate_summary(resource['id'])
    
    # Verify aggregation results
    assert summary.total_count > 0
    assert summary.approved_count >= 0
```


## Precautions

### 1. Fixture Scope

- `scope='function'`: A new instance is created for each test function
- Data independence between tests is maintained

### 2. Database Cleanup

- Using `@pytest.mark.db_test` automatically rolls back upon test completion
- Manual cleanup is unnecessary

### 3. Test Data Consistency

- Test data defined in fixtures uses fixed values
- Test reproducibility is maintained

### 4. Parallel Execution

- Parallel execution is possible as each test runs independently
- No need to consider database race conditions

