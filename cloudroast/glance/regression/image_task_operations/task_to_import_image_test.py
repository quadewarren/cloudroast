"""
Copyright 2015 Rackspace

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import calendar
import time

from cloudcafe.common.tools.datagen import rand_name
from cloudcafe.glance.common.constants import Messages
from cloudcafe.glance.common.types import TaskStatus, TaskTypes

from cloudroast.glance.fixtures import ImagesFixture


class TaskToImportImage(ImagesFixture):

    def test_task_to_import_image(self):
        """
        @summary: Create a task to import an image

        1) Create a task to import an image
        2) Verify that the response code is 201
        3) Wait for the task to complete successfully
        4) Verify that the returned task's properties are as expected
        generically
        5) Verify that the returned task's properties are as expected more
        specifically
        """

        input_ = {'image_properties': {},
                  'import_from': self.images.config.import_from}

        resp = self.images.client.task_to_import_image(
            input_, TaskTypes.IMPORT)
        self.assertEqual(resp.status_code, 201,
                         self.status_code_msg.format(201, resp.status_code))
        task_id = resp.entity.id_

        task_creation_time_in_sec = calendar.timegm(time.gmtime())

        task = self.images.behaviors.wait_for_task_status(
            task_id, TaskStatus.SUCCESS)

        errors = self.images.behaviors.validate_task(task)

        created_at_delta = self.images.behaviors.get_time_delta(
            task_creation_time_in_sec, task.created_at)
        updated_at_delta = self.images.behaviors.get_time_delta(
            task_creation_time_in_sec, task.updated_at)
        expires_at_delta = self.images.behaviors.get_time_delta(
            task_creation_time_in_sec, task.expires_at)

        if created_at_delta > self.images.config.max_created_at_delta:
            errors.append(Messages.PROPERTY_MSG.format(
                'created_at delta', self.images.config.max_created_at_delta,
                created_at_delta))
        if expires_at_delta > self.images.config.max_expires_at_delta:
            errors.append(Messages.PROPERTY_MSG.format(
                'expires_at delta', self.images.config.max_expires_at_delta,
                expires_at_delta))
        if task.owner != self.images.auth.tenant_id:
                errors.append(Messages.PROPERTY_MSG.format(
                    'owner', self.images.auth.tenant_id, task.owner))
        if task.status != TaskStatus.SUCCESS:
            errors.append(Messages.PROPERTY_MSG.format(
                'status', TaskStatus.SUCCESS, task.status))
        if updated_at_delta > self.images.config.max_updated_at_delta:
            errors.append(Messages.PROPERTY_MSG.format(
                'updated_at delta', self.images.config.max_updated_at_delta,
                updated_at_delta))

        self.assertEqual(
            errors, [],
            msg=('Unexpected error received. Expected: No errors '
                 'Received: {0}').format(errors))

    def test_task_to_import_image_duplicate(self):
        """
        @summary: Attempt to create a duplicate of the task to import image

        1) Create a task to import an image
        2) Verify that the response code is 201
        3) Wait for the task to complete successfully
        4) Create another task to import an image with the same input
        properties
        5) Verify that the response code is 201
        6) Wait for the task to complete successfully
        7) Verify that the first import task is not the same as the second
        import task
        """

        tasks = []
        input_ = {'image_properties': {},
                  'import_from': self.images.config.import_from}

        for i in range(2):
            resp = self.images.client.task_to_import_image(
                input_, TaskTypes.IMPORT)
            self.assertEqual(resp.status_code, 201,
                             self.status_code_msg.format(201,
                                                         resp.status_code))
            task_id = resp.entity.id_

            task = self.images.behaviors.wait_for_task_status(
                task_id, TaskStatus.SUCCESS)

            tasks.append(task)

        self.assertNotEqual(
            tasks[0], tasks[1],
            msg=('Unexpected tasks received. Expected: Tasks to be different '
                 'Received: {0} and {1}').format(tasks[0], tasks[1]))

    def test_multiple_simultaneous_tasks_to_import_images(self):
        """
        @summary: Create multiple tasks to import images at the same time

        1) Create multiple tasks to import images
        2) Verify that the response code is 201 for each request
        3) Wait for all tasks to complete successfully
        4) List all images
        5) Verify that all imported images are returned
        """

        tasks = []
        imported_image_ids = []
        listed_image_ids = []
        input_ = {'image_properties': {},
                  'import_from': self.images.config.import_from}

        for i in range(5):
            resp = self.images.client.task_to_import_image(
                input_, TaskTypes.IMPORT)
            self.assertEqual(resp.status_code, 201,
                             self.status_code_msg.format(201,
                                                         resp.status_code))
            tasks.append(resp.entity)

        for task in tasks:
            task = self.images.behaviors.wait_for_task_status(
                task.id_, TaskStatus.SUCCESS)
            imported_image_ids.append(task.result.image_id)

        listed_images = self.images.behaviors.list_all_images()
        [listed_image_ids.append(image.id_) for image in listed_images]

        for id_ in imported_image_ids:
            self.assertIn(id_, listed_image_ids,
                          msg=('Unexpected image id received. Expected: {0} '
                               'to be listed in {1} Received: Image not '
                               'listed').format(id_, listed_image_ids))

    def test_task_to_import_image_passing_image_name_property(self):
        """
        @summary: Create a task to import an image passing in the image name
        property

        1) Create a task to import an image passing in the image name property
        2) Verify that the response code is 201
        3) Wait for the task to complete successfully
        4) Verify that the returned task's properties are as expected
        generically
        5) Get image details
        6) Verify that the response is ok
        7) Verify that the imported image's name is as expected
        """

        name = rand_name('image')

        input_ = {'image_properties': {'name': name},
                  'import_from': self.images.config.import_from}

        resp = self.images.client.task_to_import_image(
            input_, TaskTypes.IMPORT)
        self.assertEqual(resp.status_code, 201,
                         self.status_code_msg.format(201, resp.status_code))
        task_id = resp.entity.id_

        task = self.images.behaviors.wait_for_task_status(
            task_id, TaskStatus.SUCCESS)

        errors = self.images.behaviors.validate_task(task)

        resp = self.images.client.get_image_details(task.result.image_id)
        self.assertTrue(resp.ok, self.ok_resp_msg.format(resp.status_code))
        get_image = resp.entity

        if get_image.name != name:
            errors.append(Messages.PROPERTY_MSG.format(
                'name', name, get_image.name))

        self.assertEqual(
            errors, [],
            msg=('Unexpected error received. Expected: No errors '
                 'Received: {0}').format(errors))

    def test_task_to_import_image_passing_other_properties_forbidden(self):
        """
        @summary: Create a task to import an image passing other image
        properties

        1) Create import task with other image properties
        2) Verify that the response code is 201
        3) Wait for the task to fail
        4) Verify that the failed task contains the correct message
        """

        input_ = {'image_properties': {'image_type': TaskTypes.IMPORT},
                  'import_from': self.images.config.import_from}

        resp = self.images.client.task_to_import_image(
            input_, TaskTypes.IMPORT)
        self.assertEqual(resp.status_code, 201,
                         self.status_code_msg.format(201, resp.status_code))
        task_id = resp.entity.id_

        task = self.images.behaviors.wait_for_task_status(
            task_id, TaskStatus.FAILURE)

        self.assertEqual(
            task.message, Messages.EXTRA_IMAGE_PROPERTIES_MSG,
            msg=('Unexpected message received. Expected: {0} '
                 'Received: {1}').format(Messages.EXTRA_IMAGE_PROPERTIES_MSG,
                                         task.message))