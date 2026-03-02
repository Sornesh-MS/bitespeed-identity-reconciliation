from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import SessionLocal, engine
from models import Base, Contact, LinkPrecedenceEnum
from schemas import IdentifyRequest, IdentifyResponse, ContactResponse
from typing import List

app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/identify", response_model=IdentifyResponse)
def identify(request: IdentifyRequest, db: Session = Depends(get_db)):

    if not request.email and not request.phoneNumber:
        raise HTTPException(status_code=400, detail="Email or phoneNumber required")

    # Step 1: Find matching contacts
    existing_contacts = db.query(Contact).filter(
        or_(
            Contact.email == request.email,
            Contact.phoneNumber == request.phoneNumber
        ),
        Contact.deletedAt.is_(None)
    ).all()

    # CASE 1: No contacts → create primary
    if not existing_contacts:
        new_contact = Contact(
            email=request.email,
            phoneNumber=request.phoneNumber,
            linkPrecedence=LinkPrecedenceEnum.primary
        )
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)

        return IdentifyResponse(
            contact=ContactResponse(
                primaryContactId=new_contact.id,
                emails=[new_contact.email] if new_contact.email else [],
                phoneNumbers=[new_contact.phoneNumber] if new_contact.phoneNumber else [],
                secondaryContactIds=[]
            )
        )

    # Step 2: Get all linked contacts
    contact_ids = [c.id for c in existing_contacts]
    linked_contacts = db.query(Contact).filter(
        or_(
            Contact.id.in_(contact_ids),
            Contact.linkedId.in_(contact_ids)
        )
    ).all()

    # Step 3: Find oldest as primary
    primary = min(linked_contacts, key=lambda x: x.createdAt)

    # Convert other primaries to secondary
    for contact in linked_contacts:
        if contact.id != primary.id and contact.linkPrecedence == LinkPrecedenceEnum.primary:
            contact.linkPrecedence = LinkPrecedenceEnum.secondary
            contact.linkedId = primary.id

    # Check if new info needs new secondary
    existing_emails = {c.email for c in linked_contacts if c.email}
    existing_phones = {c.phoneNumber for c in linked_contacts if c.phoneNumber}

    if (request.email and request.email not in existing_emails) or \
       (request.phoneNumber and request.phoneNumber not in existing_phones):

        new_secondary = Contact(
            email=request.email,
            phoneNumber=request.phoneNumber,
            linkedId=primary.id,
            linkPrecedence=LinkPrecedenceEnum.secondary
        )
        db.add(new_secondary)
        db.commit()
        db.refresh(new_secondary)
        linked_contacts.append(new_secondary)

    db.commit()

    # Re-fetch all contacts linked to primary
    all_contacts = db.query(Contact).filter(
        or_(
            Contact.id == primary.id,
            Contact.linkedId == primary.id
        )
    ).all()

    emails = []
    phones = []
    secondary_ids = []

    for contact in all_contacts:
        if contact.email and contact.email not in emails:
            emails.append(contact.email)
        if contact.phoneNumber and contact.phoneNumber not in phones:
            phones.append(contact.phoneNumber)
        if contact.linkPrecedence == LinkPrecedenceEnum.secondary:
            secondary_ids.append(contact.id)

    return IdentifyResponse(
        contact=ContactResponse(
            primaryContactId=primary.id,
            emails=emails,
            phoneNumbers=phones,
            secondaryContactIds=secondary_ids
        )
    )