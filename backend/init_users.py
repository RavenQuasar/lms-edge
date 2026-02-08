import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def create_default_users():
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            admin = result.scalar_one_or_none()
            
            if not admin:
                admin_user = User(
                    username="admin",
                    full_name="System Administrator",
                    role=UserRole.ADMIN,
                    password_hash=get_password_hash("admin123"),
                    avatar="admin_avatar.png"
                )
                session.add(admin_user)
                print("✓ Created admin user (username: admin, password: admin123)")
            else:
                print("✓ Admin user already exists")
            
            result = await session.execute(
                select(User).where(User.username == "teacher")
            )
            teacher = result.scalar_one_or_none()
            
            if not teacher:
                teacher_user = User(
                    username="teacher",
                    full_name="Sample Teacher",
                    role=UserRole.TEACHER,
                    password_hash=get_password_hash("teacher123"),
                    avatar="teacher_avatar.png"
                )
                session.add(teacher_user)
                print("✓ Created teacher user (username: teacher, password: teacher123)")
            else:
                print("✓ Teacher user already exists")
            
            result = await session.execute(
                select(User).where(User.username == "student")
            )
            student = result.scalar_one_or_none()
            
            if not student:
                student_user = User(
                    username="student",
                    full_name="Sample Student",
                    role=UserRole.STUDENT,
                    password_hash=get_password_hash("student123"),
                    avatar="student_avatar.png"
                )
                session.add(student_user)
                print("✓ Created student user (username: student, password: student123)")
            else:
                print("✓ Student user already exists")
            
            await session.commit()
            print("\nDefault users created successfully!")
            print("\nLogin credentials:")
            print("  Admin: admin / admin123")
            print("  Teacher: teacher / teacher123")
            print("  Student: student / student123")
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating default users: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_default_users())
