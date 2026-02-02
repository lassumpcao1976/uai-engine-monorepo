from sqlalchemy.orm import Session
from app.models.user import User
from app.models.credit import CreditTransaction, CreditTransactionType
from app.models.build import Build
from app.core.config import settings
from app.core.logging import logger


class CreditService:
    @staticmethod
    def check_balance(user: User, amount: int) -> bool:
        return user.credits >= amount

    @staticmethod
    def charge_build(user: User, build: Build, db: Session) -> bool:
        if not CreditService.check_balance(user, settings.credits_per_build):
            return False
        
        user.credits -= settings.credits_per_build
        transaction = CreditTransaction(
            user_id=user.id,
            amount=-settings.credits_per_build,
            transaction_type=CreditTransactionType.BUILD,
            description=f"Build #{build.id}",
            build_id=build.id,
        )
        db.add(transaction)
        db.commit()
        logger.info("credits_charged", user_id=user.id, amount=settings.credits_per_build, build_id=build.id)
        return True

    @staticmethod
    def charge_export(user: User, db: Session) -> bool:
        if not CreditService.check_balance(user, settings.credits_per_export):
            return False
        
        user.credits -= settings.credits_per_export
        transaction = CreditTransaction(
            user_id=user.id,
            amount=-settings.credits_per_export,
            transaction_type=CreditTransactionType.EXPORT,
            description="Project export",
        )
        db.add(transaction)
        db.commit()
        logger.info("credits_charged", user_id=user.id, amount=settings.credits_per_export, transaction_type="export")
        return True

    @staticmethod
    def refund_build(user: User, build: Build, db: Session):
        user.credits += settings.credits_per_build
        transaction = CreditTransaction(
            user_id=user.id,
            amount=settings.credits_per_build,
            transaction_type=CreditTransactionType.REFUND,
            description=f"Refund for build #{build.id}",
            build_id=build.id,
        )
        db.add(transaction)
        db.commit()
        logger.info("credits_refunded", user_id=user.id, amount=settings.credits_per_build, build_id=build.id)
