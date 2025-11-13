# Administrator Permissions

## Table of Contents
- [User Types and Permission Overview](#administrator-permissions)
- [Comment Management Screen Permissions](#permission-matrix-for-actions-in-comment-management-screen)
- [Resource Comment Screen Permissions](#permission-matrix-for-actions-in-resource-comment-screen)
- [Utilization Screen Permissions (View, Edit, Delete)](#permission-matrix-for-actions-in-utilization-screen-view-edit-delete)
- [Utilization Screen Permissions (Certification, Approval)](#permission-matrix-for-actions-in-utilization-screen-certification-approval)

* Permissions are configured for the following four types of users:
  * System Administrator
    * User with administrator privileges for the entire CKAN system
  * Organization Administrator
    * User with administrator privileges for a specific configured organization
  * Organization Members (General Users) (Editor, Member)
    * General users who can only edit datasets and resources registered in a specific organization
  * Non-logged-in Users
    * Users who are not logged in

* Permissions are granted according to the following matrix diagrams:
  * Vertical axis: Represents whether the user is logged in and the type of logged-in user
  * Horizontal axis:
    * (Row 1): Represents the actions (approve, edit, etc.) that can be performed on each screen
    * (Row 2): Represents whether a resource is registered in the user's own organization or another organization from the perspective of a user belonging to an organization
    * (Row 3): Represents whether comments or utilization methods are approved or in an unapproved state awaiting approval
      * (Example 1): In the comment management screen, organization administrators can view comments registered in their own organization regardless of approved/unapproved status (marked with ○)
      * (Example 2): In the comment management screen, organization administrators cannot view comments registered in other organizations regardless of approved/unapproved status (marked with ×)

## Permission Matrix for Actions in Comment Management Screen

### Comment Viewing / Bulk Approval・Bulk Delete

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** | ○ | ○ | ○ | ○ |
| **Organization Administrator** | ○ | ○ | × | × |
| **Organization Members (Editor, Member)** | × ※1 | × ※1 | × ※1 | × ※1 |
| **Non-logged-in** | × ※1 | × ※1 | × ※1 | × ※1 |


  **※1 The tab to navigate to the comment management screen is not displayed in the page header, and navigation to the screen is not possible even when specifying the URL (/management/comments)**

## Permission Matrix for Actions in Resource Comment Screen

### Comment Viewing

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** | ○ | ○ | ○ | ○ |
| **Organization Administrator** | ○ | ○ | ○ | × |
| **Organization Members (Editor, Member)** | ○ | × | ○ | × |
| **Non-logged-in** | ○ | × | ○ | × |

### Reply to Comments

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** | ○ | ○ | ○ | ○ |
| **Organization Administrator** | ○ | × | × | × |
| **Organization Members (Editor, Member)** | × | × | × | × |
| **Non-logged-in** | × | × | × | × |

### Approval Action

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** |  | ○ |  | ○ |
| **Organization Administrator** |  | ○ |  | × |
| **Organization Members (Editor, Member)** |  | × |  | × |
| **Non-logged-in** |  | × |  | × |

## Permission Matrix for Actions in Utilization Screen (View, Edit, Delete)

### Utilization Viewing

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** | ○ | ○ | ○ | ○ |
| **Organization Administrator** | ○ | ○ | ○ ※1| × |
| **Organization Members (Editor, Member)** | ○ ※2 | × | ○ ※2 | × |
| **Non-logged-in** | ○ ※2 | × | ○ ※2 | × |

### Utilization Edit・Delete

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** | ○ | ○ | ○ | ○ |
| **Organization Administrator** | ○ | ○ | × | × |
| **Organization Members (Editor, Member)** | × | × | × | × |
| **Non-logged-in** | × | × | × | × |

  **※1 Status column is displayed but remains blank**  
  **※2 Status column is not displayed**

## Permission Matrix for Actions in Utilization Screen (Certification, Approval)

### Utilization Issue Resolution Certification

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** | ○ | ○ | ○ | ○ |
| **Organization Administrator** | ○ | ○ | × | × |
| **Organization Members (Editor, Member)** | × | × | × | × |
| **Non-logged-in** | × | × | × | × |

### Approval of Comments on Utilization

|  | Own Organization<br>(Approved) | Own Organization<br>(Unapproved) | Other Organizations<br>(Approved) | Other Organizations<br>(Unapproved) |
|--------------|:-------:|:-------:|:-------:|:-------:|
| **System Administrator** |  | ○ |  | ○ |
| **Organization Administrator** |  | ○ |  | × |
| **Organization Members (Editor, Member)** |  | × |  | × |
| **Non-logged-in** |  | × |  | × |


