# Adding Sort Options to Dataset List Screen

Add sort options for number of likes and downloads to the dataset list screen.

![Dataset Sort Feature - Likes Image](../assets/dataset_sort_30.jpg)

## Overview

**This feature works when the Like and Download functions of the feedback plugin are enabled.**


## Key Features



### Sort by Number of Likes

You can sort datasets in descending order by number of likes.

![Dataset Sort Feature - Likes Image](../assets/dataset_sort_10.jpg)



### Sort by Number of Downloads

You can sort datasets in descending order by number of downloads.

![Dataset Sort Feature - Downloads Image](../assets/dataset_sort_20.jpg)


## Configuration

### Important Notes

When applying this feature to existing datasets, you need to run the following commands:



```bash
# Rebuild search index for all datasets
ckan -c /path/to/ckan.ini search-index rebuild

# Rebuild search index for specific dataset only
ckan -c /path/to/ckan.ini search-index rebuild <dataset-name> 
```

To find datasets that need to be reindexed, run the following command:

```bash
# Check for datasets that are not indexed
ckan -c /path/to/ckan.ini search-index check
```

> [!IMPORTANT]
> The `ckan` command must be executed where `ckan.ini` is located, or the `ckan.ini` path must be specified with `-c`.

[Command Reference Page](https://docs.ckan.org/en/latest/maintaining/cli.html#search-index-rebuild-search-index)


---


For ON/OFF settings of each feature, please refer to the following document:

📖 [Detailed Documentation on ON/OFF Features](./switch_function.md)

