/* ----------------------------------------------------------------------------
 * This file was automatically generated by SWIG (http://www.swig.org).
 * Version 3.0.10
 *
 * Do not make changes to this file unless you know what you are doing--modify
 * the SWIG interface file instead.
 * ----------------------------------------------------------------------------- */

package bc;

public class VecUnitType {
  private transient long swigCPtr;
  protected transient boolean swigCMemOwn;

  protected VecUnitType(long cPtr, boolean cMemoryOwn) {
    swigCMemOwn = cMemoryOwn;
    swigCPtr = cPtr;
  }

  protected static long getCPtr(VecUnitType obj) {
    return (obj == null) ? 0 : obj.swigCPtr;
  }

  protected void finalize() {
    delete();
  }

  public synchronized void delete() {
    if (swigCPtr != 0) {
      if (swigCMemOwn) {
        swigCMemOwn = false;
        bcJNI.delete_VecUnitType(swigCPtr);
      }
      swigCPtr = 0;
    }
  }

  public VecUnitType() {
    this(bcJNI.new_VecUnitType(), true);
  }

  public String toString() {
    return bcJNI.VecUnitType_toString(swigCPtr, this);
  }

  public VecUnitType clone() {
    long cPtr = bcJNI.VecUnitType_clone(swigCPtr, this);
    return (cPtr == 0) ? null : new VecUnitType(cPtr, true);
  }

  public long size() {
    return bcJNI.VecUnitType_size(swigCPtr, this);
  }

  public UnitType get(long index) {
    return UnitType.swigToEnum(bcJNI.VecUnitType_get(swigCPtr, this, index));
  }

}
