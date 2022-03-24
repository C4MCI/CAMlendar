document.addEventListener('DOMContentLoaded', function () {
    var calendarEl = document.getElementById('calendar');
    let myModal = new bootstrap.Modal(document.getElementById('myModal'));
    let frm = document.getElementById('event-form');
    let deletebtn = document.getElementById('btnDelete');
    var base_url = window.location.origin;

    var calendar = new FullCalendar.Calendar(calendarEl, {
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
        },
        navLinks: true, // can click day/week names to navigate views
        businessHours: true, // display business hours
        firstDay: 1,
        selectHelper: true,
        eventStartEditable: true,
        selectable: true,
        events: base_url + "/list",
        select: function (selectionInfo) {
            if (selectionInfo.allDay) {
                frm.reset();
                document.getElementById("btnDelete").classList.add('d-none');
                document.getElementById("title").textContent = "Register Event";
                document.getElementById("startDate").value = selectionInfo.startStr;
                document.getElementById("endDate").value = selectionInfo.endStr;
                document.getElementById("startTime").value = '00:00';
                document.getElementById("endTime").value = '00:00';
                document.getElementById("id").value = "";
            }
            else {
                frm.reset();
                document.getElementById("btnDelete").classList.add('d-none');
                document.getElementById("title").textContent = "Register Event";
                document.getElementById("startDate").value = selectionInfo.start.toISOString().slice(0, -14);
                document.getElementById("endDate").value = selectionInfo.end.toISOString().slice(0, -14);
                document.getElementById("startTime").value = selectionInfo.startStr.slice(11, -9);
                document.getElementById("endTime").value = selectionInfo.endStr.slice(11, -9);
                document.getElementById("id").value = "";
            }

            myModal.show();
        },

        eventClick: function (info) {
            document.getElementById("btnDelete").classList.remove('d-none');
            document.getElementById("title").textContent = "Modify Event";
            document.getElementById("event").value = info.event.title;
            document.getElementById("startDate").value = info.event.startStr.slice(0, -15);
            document.getElementById("endDate").value = info.event.endStr.slice(0, -15);
            document.getElementById("startTime").value = info.event.startStr.slice(11, -9);
            document.getElementById("endTime").value = info.event.endStr.slice(11, -9);
            document.getElementById("id").value = info.event.id;

            myModal.show();
        },

        eventDrop: function (info) {

            var startDate = info.event.startStr.slice(0, -15);
            var endDate = info.event.endStr.slice(0, -15);
            var startTime = info.event.startStr.slice(11, -9);
            var endTime = info.event.endStr.slice(11, -9);
            var id = info.event.id;

            url = base_url + "/drop/" + id + "/" + startDate + "T" + startTime + "/" + endDate + "T" + endTime;

            window.location.replace(url);


        }



    });

    calendar.render();

    deletebtn.addEventListener('click', function () {
        myModal.hide();
        Swal.fire({
            title: 'Delete Event?',
            text: "This event will be deleted!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Yes, delete it!'
        }).then((result) => {
            if (result.isConfirmed) {
                const url = base_url + "/delete/" + document.getElementById('id').value;
                window.location.replace(url);
            }
        })
    });


});

