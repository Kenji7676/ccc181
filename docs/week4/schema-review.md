# Schema Review

## Entry 1: One active ticket per student

| | |
| --- | --- |
| **Works well** | The schema stores facts and computes results (question 3). `tickets` keeps only `created_at` and `called_at`, with no stored position, count or waiting time. Those are computed from `stage`, `status` and `created_at`, so nothing has to be rewritten when someone joins or leaves, and My place and the staff dashboard can never disagree about who is next (FR-02, FR-06, FR-11). |
| **Problem** | A double tap, or the same student submitting from two tabs, could create two active tickets for the same service (found with question 4). `users.student_id` is UNIQUE, but that only prevents duplicate people, not duplicate tickets, and the JavaScript double-submit guard works in only one browser tab. |
| **Change** | I added a partial unique index on `tickets(user_id, service_id)` where status is `waiting` or `called`, so a student can hold only one active ticket per service. I also added FR-12 so the rule has an ID, and added a note under the ERD, since an index adds no tables or lines. |

```sql
CREATE UNIQUE INDEX one_active_ticket_per_service
  ON tickets (user_id, service_id)
  WHERE status IN ('waiting', 'called');
```

## Entry 2: Theme choice has no home in the database

| | |
| --- | --- |
| **Works well** | Every fact lives in one place (question 2). A person's name and Student ID are stored only in `users`, and a service's name only in `services`. Tickets store `user_id` and `service_id` instead of copies, so renaming "Buy merch" (FR-09) changes one row and every old ticket follows. |
| **Problem** | FR-10 (light and dark mode) says Stores data = Yes, but no table or column holds a theme choice (found with question 1). |
| **Change** | I changed FR-10 to Stores data = No. The app has no accounts, so the choice is saved in the browser and the ERD stays the same. If accounts arrive later, a `theme` column on `users` is where it would go. |

## Entry 3: Leaving the queue looks like a no-show

| | |
| --- | --- |
| **Works well** | Both foreign keys use `RESTRICT` on purpose (question 5). A service or user that has tickets cannot be deleted, so the old tickets staff need for reports never disappear. A service is retired by switching off `is_active` instead. |
| **Problem** | The app marks a customer who leaves as `no-show`, so leaving and a real no-show look the same in the data (found with question 1). Lola's reports need to tell who walked away from who never showed up (FR-03, FR-05). The schema already allows a `left` status, but the app never uses it. |
| **Change** | I kept `left` in the `status` CHECK, and changed the leave route to set `left` instead of `no-show`. The ERD lists the five status values, so the diagram only needed a note. |