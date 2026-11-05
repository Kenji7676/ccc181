# Lang-Q-t requirements

**Setting:** Langkit University Shop, Monday to Saturday<br>
**People who wait:** MSU-IIT constituents buying Langkit merchandise (e.g. Ben Enben in [docs/week3/personas.md](week3/personas.md))<br>
**People who serve:** Staff operating the cashier at the shop (e.g. Lola Amour in [docs/week3/personas.md](week3/personas.md))

**Problem statement:** Ben needs a way to queue in line while still being able to browse for merchandise from the shop because he has very little extra time to compete with a very crowded Langkit shop customer base given his hectic class schedule.


# Functional requirements

| ID | Requirement | Priority | Stores data? | Status |
| --- | --- | --- | --- | --- |
| FR-01 | A customer can join the queue by choosing a service and entering their name and Student ID, and receive a ticket number in under 2 minutes without help. | Must | **Yes** | Built (Week 3) |
| FR-02 | A customer can see their ticket number, status and how many people are ahead of them in their queue within 10 seconds of opening My place. | Must | No | Built (Week 3) |
| FR-03 | A customer can exit the queue before being served, after which the ticket no longer appears on the staff list. | Must | **Yes** | Built (Week 3) |
| FR-04 | A staff member can see the called and waiting tickets in queue order and filter them by service. | Must | No | Built (Week 3) |
| FR-05 | A staff member can call the next person and mark them as served or no-show, and the customer's My place page shows the new status within 10 seconds. | Must | **Yes** | Built (Week 3) |
| FR-06 ★ | A customer who is ready to pay is called before customers who are still browsing, regardless of who joined first. | Must | No | Built (Week 3) |
| FR-07 ★ | A customer who is still browsing at Buy merch can tell the system they are ready to pay, and moves into the paying group. | Must | **Yes** | Built (Week 3) |
| FR-08 ★ | A student can join only with a Student ID in the format 0000-0000; any other ID is refused with a message showing the correct format. | Must | **Yes** | Built (Week 3) |
| FR-09 | A staff member can add, rename and switch off a service. | Should | **Yes** | Built (Week 4) |
| FR-10 | A customer can switch to either Light or Dark mode. | Could | No | Later |
| FR-11 | A customer whose ticket has been called has 3 minutes to reach the counter, sees a countdown and a warning when 1 minute is left, and the ticket is marked no-show automatically if the time runs out. | Should | **Yes** | Later |
| FR-12 ★ | A student can hold only one active ticket per service at a time; joining again while one is waiting or called is refused with a message showing their existing ticket. | Should | **Yes** | Built (Week 4) |

**MVP:** FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08<br>
**Out of scope:** FR-09 (since the Langkit University Shop doesn't offer other services aside from the two listed as of the moment), FR-10 (the feature is simply a Quality of Life improvement so it isn't that needed)


# Non-functional requirements

| ID | Requirement | Category | Priority |
| --- | --- | --- | --- |
| NFR-01 | No ticket is lost when the server or the database restarts. | Reliability | Must |
| NFR-02 | Two people can never get the same ticket, even if they join at the same moment. | Data integrity | Must |
| NFR-03 | My place loads in under 2 seconds on mobile data. | Performance | Should |
| NFR-04 | Every screen scores 90 or higher in the Lighthouse accessibility check. | Accessibility | Must |
| NFR-05 | Body text is at least 16 px and the ticket number on My place is at least 48 px, so a person with poor eyesight can read the screen without zooming (small labels excepted). | Usability | Must |
| NFR-06 | The staff dashboard still loads in under 2 seconds with 200 active tickets in the queue. | Scalability | Should |
| NFR-07 | Every screen works at 375 px wide with no sideways page scrolling, in current Chrome, Edge and Firefox. | Compatibility | Must |
| NFR-08 | A customer's name and Student ID are never shown on another customer's screen; My place shows only the customer's own ticket. | Privacy | Must |
| NFR-09 | Submitting any form with empty, very long or unexpected input shows a message and never a server error page. | Robustness | Should |
| NRF-10 | The app handles thousands of simultaneous users without slowing down or failing. | Scalability | Could |
| NRF-11 | The app keeps working offline, or can be installed as a phone app. | Availability | Could |

**MVP:** NFR-01, NFR-02, NRF-04, NFR-05, NFR-07, NFR-08<br>
**Out of scope:** NRF-10 (during operating hours, the chances of customers nearing a thousand is extremely low), NRF-11 (the app relies on live data for real-time updates so an offline mode or a native app version would affect compatibility)


# Check your requirements with a real person

| Who (role only, no full name) | What they said | What I changed |
| --- | --- | --- |
| MSU-IIT student | "Anything missing that I would add is a time limit system on how long a person can wait until it is considered "no-show" (notified to users in advanced)." | I added **FR-11 (Should):** a customer whose ticket has been called now has 3 minutes to reach the counter. My place shows a countdown and a warning when 1 minute is left, and the system marks the ticket as no-show automatically if time runs out. The rule is also shown in advance on the Join page and the My place page. |
