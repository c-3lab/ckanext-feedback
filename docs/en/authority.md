# Administrator Privileges

- The following four types of users have different permissions:
  - **sysadmin user**
    - A user with administrator privileges for the entire CKAN instance
  - **Organization admin user**
    - A user with administrator privileges for a specific Organization
  - **Organization regular user (Editor, Member)**
    - A regular user who can only edit Datasets and Resources registered under a specific Organization
  - **User not logged in**
    - A user who is not logged in

- Permissions are granted based on the matrix diagram below:
  - **Vertical axis**: Indicates whether the user is logged in or not, and if logged in, which type of user they are.
  - **Horizontal axis**:
    - (First row): Actions that can be performed on each screen (approval, edit, etc.)
    - (Second row): From the perspective of a user belonging to an Organization, whether the Resource is registered under their own Organization or under another Organization.
    - (Third row): Whether comments and utilization methods are “Approved” or in a “Waiting” state (before approval).
      - (Example 1): On the comment management screen, an Organization admin user can view comments registered under their own Organization, regardless of whether they are approved or waiting (indicated with “◯”).
      - (Example 2): On the comment management screen, an Organization admin user cannot view comments registered under other Organizations, regardless of whether they are approved or waiting (indicated with “×”).

- **Matrix diagram summarizing permissions for actions on the comment management screen**  
  ![Matrix diagram summarizing permissions for actions on the comment management screen](../assets/authority_management_comment.png)

  *Note 1: The tab for transitioning to the comment management screen does not appear in the page header, and specifying the URL (`/management/comments`) does not allow navigation to the screen.*

- **Matrix diagram summarizing permissions for actions on the Resource comment screen**  
  ![Matrix diagram summarizing permissions for actions on the Resource comment screen](../assets/authority_resource_comment.png)

- **Matrix diagram summarizing permissions for actions on the Utilization screen (view, edit, delete)**  
  ![Matrix diagram summarizing permissions for actions on the Utilization screen (view, edit, delete)](../assets/authority_utilization_crud.png)

  *Note 1: The “Status” field is displayed but remains empty.*  
  *Note 2: The “Status” field is not displayed.*

- **Matrix diagram summarizing permissions for actions on the Utilization screen (certification, approval)**  
  ![Matrix diagram summarizing permissions for actions on the Utilization screen (certification, approval)](../assets/authority_utilization_approve.png)
