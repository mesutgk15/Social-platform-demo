# COMMUNE
#### Video Demo:  https://youtu.be/4IZiL_xc8dU
#### Description:
Commune is a demo project of a family platform that you can register and create your profile. 

At registration user needs to meet the requirements, must proive name, last name, birth-date (date given after the date that time will be rejected), username(checks and denies if it was already taken), email(checks and denies if it was already taken), password(must contain at least one of each following: letter (a-z), capital letter (A-Z), digit (0-9) and between 6-12 characters long),
password confirmation (must match with the password input). A 5 digit token will be sent to given email address and ask for it in the next page, in case of match register will be completed and user will be logged in.

At login, there is two option with username or email, user can login with the preferred one. If the password hash returns true value logges user in. 

In profile page user can upload/delete a profile picture. Only jpeg or jpg file formats will be allowed, others triggers relevant error message. Address, phone number can be also added, edited or deleted. Data given here can be displayed in the family members list page.

Member list page lists all family members with their basic information as name, last name, birth date, the date they joined the Commune and their contact card. Contact card displays all personal info provided in profile page with profile picture. 

In wall page, users can post, like or dislike messages. Does not allow more than one like or dislike or both at the same time. Icons change depending on users like/dislike status for that post. Like dislike counts are displayed in the footer of each post. Posting time is given with the owner of the post in header. System posts automatic updates on this wall page when a user creates a poll, joins or leaves the family with a timestamp. When user clicks new post a modal form pops up for post content rather than redirecting to a new page.

Polls page lists all polls created by family members. When go to start new poll page. You need to select a deadline for the poll, cannot be backdated. Votes will be blocked after this date. Max selections will alse be defined at this step, the formula in javascript will be called when polls are listed and will block selections exceeding this max. selection. Add selection button adds empty selection boxes, when you remove a box from middle the following boxes decreases by one. Question must be filled and there must be at least two filled selections (max selection checks dependent on number of selections.) It will be allowed to vote for only once for each poll for each user. Percentages of each selection and voter/total member ratio will be displayed with each poll. 



