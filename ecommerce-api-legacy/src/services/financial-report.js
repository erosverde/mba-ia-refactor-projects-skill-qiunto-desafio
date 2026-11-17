async function financialReport(store) {
    const courses = new Map();
    for (const row of await store.financialRows()) {
        if (!courses.has(row.course_id)) {
            courses.set(row.course_id, { course: row.title, revenue: 0, students: [] });
        }
        if (row.enrollment_id === null) continue;
        const course = courses.get(row.course_id);
        if (row.status === 'PAID') course.revenue += row.amount;
        course.students.push({ student: row.student ?? 'Unknown', paid: row.amount ?? 0 });
    }
    return Array.from(courses.values());
}

module.exports = { financialReport };
