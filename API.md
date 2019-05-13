# rm-reporting endpoints

This page documents the rm-reporting endpoints that can be hit.

## Info endpoints

* `/info`
GET request to this endpoint displays the name of the service and its version number.

## Response chasing endpoints

`/download-report/<collection_exercise_id>/<survey_id>`
* GET request to this endpoint fetches a report about a collection exercise.
* `collection_exercise_id` is the ID of the collection exercise.
* `survey_id` is the ID of the survey.

`/download-social-mi/<collection_exercise_id>`
* GET request to this endpoint fetches a social MI report.
* `collection_exercise_id` is the ID of the collection exercise.

## Responses dashboard endpoints

`/survey/<survey_id>/collection-exercise/<collection_exercise_id>`
* GET request to this endpoint fetches a survey report.
* `collection_exercise_id` is the ID of the collection exercise.
* `survey_id` is the ID of the survey.