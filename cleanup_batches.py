# cleanup_batches.py
from app import create_app, db
from app.models import Batch, Job

app = create_app()

with app.app_context():
    print("Starting batch cleanup...\n")

    all_batches = Batch.query.all()
    bad_batches = []

    for batch in all_batches:
        # Find batches with commas (bad data)
        if ',' in batch.name:
            bad_batches.append(batch)

    print(f"Found {len(bad_batches)} bad batch entries")

    for batch in bad_batches:
        print(f"\nProcessing: {batch.name}")
        jobs = batch.jobs[:]  # Copy list to avoid modification during iteration

        # Split into individual batch names
        batch_names = [name.strip() for name in batch.name.split(',') if name.strip()]

        for name in batch_names:
            # Find or create individual batch
            individual_batch = Batch.query.filter_by(name=name).first()
            if not individual_batch:
                individual_batch = Batch(name=name)
                db.session.add(individual_batch)
                print(f"  ✓ Created batch: {name}")

            # Link to all jobs that had the combined batch
            for job in jobs:
                if individual_batch not in job.batches:
                    job.batches.append(individual_batch)
                    print(f"  ✓ Linked {name} to: {job.title}")

        # Remove the bad batch
        db.session.delete(batch)
        print(f"  ✗ Deleted bad batch: {batch.name}")

    db.session.commit()

    print("\n" + "=" * 50)
    print("Cleanup complete!")
    print("=" * 50)

    # Show final batch list
    remaining_batches = Batch.query.order_by(Batch.name.desc()).all()
    print(f"\nFinal batch list ({len(remaining_batches)} batches):")
    for batch in remaining_batches:
        job_count = len(batch.jobs)
        print(f"  • {batch.name} ({job_count} jobs)")